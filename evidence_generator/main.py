import os
import hashlib
import psycopg2
import psycopg2.extras
import shutil
import uuid
from datetime import datetime, timezone
from renderer import render_pdf, render_image

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

STORAGE_PATH = os.getenv("CIVIX_EVIDENCE_STORE_PATH", r"c:\data\civix_demo\evidence_store")

def calculate_sha256(filepath):
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.digest()

def get_admin_user_id(cur):
    cur.execute("SELECT user_id FROM civix.civix_user WHERE username = 'civix_system'")
    row = cur.fetchone()
    if row:
        return row[0]
    return None

def main():
    if not os.path.exists(STORAGE_PATH):
        os.makedirs(STORAGE_PATH, exist_ok=True)
        
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    admin_id = get_admin_user_id(cur)
    if not admin_id:
        print("Admin user not found. Exiting.")
        return
        
    cur.execute("""
        SELECT manifest_id, case_id, source_record_id, evidence_id_str, evidence_type, title, prompt, expected_mime_type 
        FROM civix.evidence_generation_manifest 
        WHERE generation_status = 'PENDING'
    """)
    rows = cur.fetchall()
    print(f"Found {len(rows)} pending evidence artifacts to generate.")
    
    for row in rows:
        manifest_id, case_id, source_record_id, ev_id, ev_type, title, prompt, mime_type = row
        print(f"Generating {ev_id}...")
        
        # Determine extension and rendering method
        if mime_type == "application/pdf":
            ext = ".pdf"
            render_func = render_pdf
        else:
            ext = ".png"
            render_func = render_image
            
        temp_filepath = os.path.join(STORAGE_PATH, f"temp_{ev_id}{ext}")
        
        try:
            # 1. Generate Bytes
            render_func(temp_filepath, ev_id, ev_type, title, prompt)
            
            # 2. Hash Bytes
            file_hash = calculate_sha256(temp_filepath)
            file_size = os.path.getsize(temp_filepath)
            
            # 3. Store Atomic Copy (Content Addressed)
            hex_hash = file_hash.hex()
            final_filename = f"{hex_hash}{ext}"
            final_filepath = os.path.join(STORAGE_PATH, final_filename)
            
            if not os.path.exists(final_filepath):
                shutil.move(temp_filepath, final_filepath)
            else:
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath) # Hash collision, identical file exists
            
            # 4. Insert Artifact Row
            cur.execute("""
                SELECT artifact_id FROM civix.evidence_artifact 
                WHERE sha256_hash = %s AND hash_algorithm = 'SHA256'
            """, (file_hash,))
            existing = cur.fetchone()
            
            if existing:
                artifact_id = existing[0]
            else:
                artifact_id = str(uuid.uuid4())
                metadata = psycopg2.extras.Json({
                    "evidence_type": ev_type,
                    "title": title,
                    "generated_from_manifest": manifest_id
                })
                cur.execute("""
                    INSERT INTO civix.evidence_artifact
                        (artifact_id, sha256_hash, hash_algorithm, file_size_bytes, mime_type, original_filename, storage_uri, media_metadata)
                    VALUES (%s, %s, 'SHA256', %s, %s, %s, %s, %s)
                """, (artifact_id, file_hash, file_size, mime_type, f"{ev_id}{ext}", final_filename, metadata))
                
            # 5. Insert Evidence Instance
            instance_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO civix.evidence_instance
                    (instance_id, artifact_id, case_id, source_record_id, acquired_by, acquisition_method, legal_status)
                VALUES (%s, %s, %s, %s, %s, 'GENERATED_SEED', 'ACTIVE')
                ON CONFLICT DO NOTHING
            """, (instance_id, artifact_id, case_id, source_record_id, admin_id))
            
            # 6. Update Manifest
            cur.execute("""
                UPDATE civix.evidence_generation_manifest
                SET generation_status = 'GENERATED', artifact_id = %s, updated_at = now()
                WHERE manifest_id = %s
            """, (artifact_id, manifest_id))
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            print(f"Error generating {ev_id}: {e}")
            cur.execute("""
                UPDATE civix.evidence_generation_manifest
                SET generation_status = 'FAILED', updated_at = now()
                WHERE manifest_id = %s
            """, (manifest_id,))
            conn.commit()
            
    conn.close()
    print("Generation complete.")

if __name__ == "__main__":
    main()

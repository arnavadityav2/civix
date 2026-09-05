import os
import shutil
import psycopg2

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
GALLERY_STORE = r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\bf4a8aa4-a234-490d-996a-eaf4002a7145\gallery_samples"

def reset_all():
    print("--- STARTING COMPLETE EVIDENCE IMAGE RESET ---")
    
    # 1. Delete image files from disk
    deleted_files = 0
    if os.path.exists(EVIDENCE_STORE):
        for f in os.listdir(EVIDENCE_STORE):
            if f.endswith(".png"):
                file_path = os.path.join(EVIDENCE_STORE, f)
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception as e:
                    print(f"Warning: Failed to delete {f}: {e}")
                    
    print(f"Deleted {deleted_files} PNG image files from {EVIDENCE_STORE}")
    
    # 2. Clear gallery samples
    if os.path.exists(GALLERY_STORE):
        shutil.rmtree(GALLERY_STORE, ignore_errors=True)
        os.makedirs(GALLERY_STORE, exist_ok=True)
        print(f"Cleared gallery samples folder.")

    # 3. Reset PostgreSQL database tables
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER USER;")
        
        # Unique placeholder hash per artifact
        cur.execute("""
            UPDATE civix.evidence_artifact
            SET sha256_hash = digest(artifact_id::text, 'sha256'),
                storage_uri = NULL,
                file_size_bytes = 0,
                processed_at = NULL
            WHERE artifact_id IN (
                SELECT artifact_id FROM civix.evidence_generation_manifest WHERE expected_mime_type = 'image/png'
            );
        """)
        updated_artifacts = cur.rowcount
        
        # Reset manifest status
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET generation_status = 'PENDING', updated_at = NOW()
            WHERE expected_mime_type = 'image/png';
        """)
        updated_manifests = cur.rowcount
        
        cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER USER;")
        
        print(f"Reset {updated_artifacts} evidence_artifact records in PostgreSQL.")
        print(f"Reset {updated_manifests} evidence_generation_manifest records to PENDING status.")
        
    finally:
        conn.close()
        
    print("--- FRESH CLEAN RESET COMPLETE! ---")

if __name__ == "__main__":
    reset_all()

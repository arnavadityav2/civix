import os
import sys
import shutil
import psycopg2

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"

def ingest_images(source_folder):
    if not os.path.exists(source_folder):
        print(f"Error: Folder '{source_folder}' does not exist!")
        return

    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()

    cur.execute("""
        SELECT m.evidence_id_str, a.storage_uri
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
        JOIN civix.evidence_instance ei ON a.artifact_id = ei.artifact_id
        JOIN civix.investigative_case c ON ei.case_id = c.case_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY c.case_number, m.evidence_id_str;
    """)

    rows = cur.fetchall()
    print(f"Loaded {len(rows)} evidence target mappings from database...")

    success_count = 0
    for idx, (ev_id, target_filename) in enumerate(rows, 1):
        # Look for 1.png, 1.jpg, 001.png, etc.
        possible_names = [
            f"{idx}.png", f"{idx}.jpg", f"{idx}.jpeg", f"{idx}.webp",
            f"{idx:03d}.png", f"{idx:03d}.jpg"
        ]
        
        found_source = None
        for name in possible_names:
            p = os.path.join(source_folder, name)
            if os.path.exists(p):
                found_source = p
                break
                
        if found_source:
            target_path = os.path.join(EVIDENCE_STORE, target_filename)
            shutil.copy2(found_source, target_path)
            success_count += 1
            print(f"[{idx}/180] Ingested '{os.path.basename(found_source)}' -> {target_filename[:16]}... ({ev_id})")
        else:
            print(f"[{idx}/180] Skipping {idx}.png (not found in {source_folder})")

    conn.close()
    print(f"\nCompleted! {success_count}/{len(rows)} images successfully ingested into {EVIDENCE_STORE}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python database/ingest_manual_images.py <path_to_images_folder>")
    else:
        ingest_images(sys.argv[1])

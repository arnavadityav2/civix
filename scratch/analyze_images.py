import os
import glob
import hashlib
import psycopg2

desktop_dir = r"C:\Users\ARNAV ADITYA\Desktop\images"
image_files = sorted(os.listdir(desktop_dir))
print(f"Total files in Desktop/images: {len(image_files)}")

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
cur = conn.cursor()

cur.execute("""
    SELECT artifact_id, original_filename, storage_uri, mime_type
    FROM civix.evidence_artifact
    WHERE mime_type LIKE 'image/%'
    ORDER BY artifact_id
""")
db_artifacts = cur.fetchall()
print(f"Total image artifacts in DB: {len(db_artifacts)}")

# Check exact filename matches
match_count = 0
for art_id, orig_fn, store_uri, mime in db_artifacts:
    if orig_fn in image_files:
        match_count += 1

print(f"Direct exact filename matches: {match_count} / {len(db_artifacts)}")

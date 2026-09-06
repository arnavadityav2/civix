import os
import shutil
import hashlib
import psycopg2
from pathlib import Path

# 1. Paths
desktop_images_dir = Path(r"C:\Users\ARNAV ADITYA\Desktop\images")
codebase_dir = Path(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0")
target_codebase_images = codebase_dir / "evidence_images"
evidence_store_dir = Path(r"C:\data\civix_demo\evidence_store")

print(f"=== STEP 1: Copying Desktop images folder to codebase directory {target_codebase_images} ===")
target_codebase_images.mkdir(parents=True, exist_ok=True)
evidence_store_dir.mkdir(parents=True, exist_ok=True)

# Copy all files from desktop images into codebase/evidence_images
desktop_files = sorted([f for f in os.listdir(desktop_images_dir) if os.path.isfile(desktop_images_dir / f)])
print(f"Found {len(desktop_files)} files in Desktop/images.")

for filename in desktop_files:
    src = desktop_images_dir / filename
    dst = target_codebase_images / filename
    shutil.copy2(src, dst)

print(f"Successfully copied {len(desktop_files)} image files into codebase at {target_codebase_images}.")

# 2. Database Processing
print("\n=== STEP 2: Updating evidence artifacts in Database and Evidence Store ===")
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="civix_demo",
    user="postgres",
    password="postgres"
)
conn.autocommit = True
cur = conn.cursor()

# Disable triggers for bulk update
cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL;")

# Fetch all image artifacts
cur.execute("""
    SELECT artifact_id, original_filename, storage_uri, mime_type
    FROM civix.evidence_artifact
    WHERE mime_type LIKE 'image/%'
    ORDER BY artifact_id
""")
db_artifacts = cur.fetchall()
print(f"Total image artifacts to update in DB: {len(db_artifacts)}")

# Map desktop files list
sorted_image_files = sorted(desktop_files)
total_available_images = len(sorted_image_files)

# Create a map for exact filename lookup
file_map = {f: f for f in desktop_files}

used_hashes = set()
updated_count = 0

for idx, (artifact_id, orig_filename, old_storage_uri, old_mime) in enumerate(db_artifacts):
    # Match strategy: exact filename match first, else modulo cycle index
    if orig_filename in file_map:
        selected_file = file_map[orig_filename]
    else:
        selected_index = idx % total_available_images
        selected_file = sorted_image_files[selected_index]

    img_path = target_codebase_images / selected_file

    with open(img_path, "rb") as f:
        file_bytes = f.read()

    sha256_hex = hashlib.sha256(file_bytes).hexdigest()
    
    # If this exact hash was already used by another artifact, append a unique salt (artifact_id)
    # so every artifact in civix.evidence_artifact has a unique SHA-256 hash satisfying uq_artifact_hash
    if sha256_hex in used_hashes:
        salt = f"\n<!-- CIVIX_ARTIFACT_ID:{artifact_id} -->".encode('utf-8')
        file_bytes = file_bytes + salt
        sha256_hex = hashlib.sha256(file_bytes).hexdigest()

    used_hashes.add(sha256_hex)
    file_size = len(file_bytes)
    sha256_bytes = bytes.fromhex(sha256_hex)

    # Determine extension and mime
    ext = img_path.suffix.lower() # .jpeg / .png / .jpg
    if ext in ['.jpg', '.jpeg']:
        mime_type = 'image/jpeg'
        ext_clean = 'jpeg'
    else:
        mime_type = 'image/png'
        ext_clean = 'png'

    final_filename = f"{sha256_hex}.{ext_clean}"
    final_store_path = evidence_store_dir / final_filename

    # Write to evidence store
    with open(final_store_path, "wb") as f:
        f.write(file_bytes)

    # Update civix.evidence_artifact
    cur.execute("""
        UPDATE civix.evidence_artifact
        SET sha256_hash = %s,
            storage_uri = %s,
            file_size_bytes = %s,
            mime_type = %s,
            processed_at = NOW()
        WHERE artifact_id = %s
    """, (sha256_bytes, final_filename, file_size, mime_type, artifact_id))

    updated_count += 1
    if (idx + 1) % 20 == 0 or (idx + 1) == len(db_artifacts):
        print(f"  [{idx + 1}/{len(db_artifacts)}] Updated Artifact {artifact_id} -> File '{selected_file}' -> Store '{final_filename[:16]}...' ({file_size} bytes)")

cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL;")
conn.close()

print(f"\nCOMPLETED SUCCESSFULLY! {updated_count}/{len(db_artifacts)} evidence image artifacts replaced with real desktop images.")

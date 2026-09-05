import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("POSTGRES_DB", "civix_demo")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id = cur.fetchone()[0]

cur.execute("""
    SELECT ea.artifact_id, ea.original_filename, ea.mime_type, ea.storage_uri
    FROM civix.evidence_artifact ea
    JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
    WHERE ei.case_id = %s
""", (case_id,))

rows = cur.fetchall()
store_root = Path(r"c:\data\civix_demo\evidence_store")

found_count = 0
for r in rows:
    aid, fname, mime, uri = r
    if not uri:
        print(f"MISSING URI: {aid} {fname}")
        continue
    
    # Try direct resolve
    target_path = store_root / uri
    if not target_path.exists():
        if uri.startswith("local://civix_evidence_store/"):
            rel = uri.removeprefix("local://civix_evidence_store/")
            target_path = store_root / rel
        else:
            # Try searching store_root recursively for filename
            matches = list(store_root.glob(f"**/{uri}"))
            if matches:
                target_path = matches[0]

    if target_path.exists():
        found_count += 1
    else:
        print(f"NOT FOUND ON DISK: {aid} | {fname} | URI: {uri}")

print(f"Successfully resolved {found_count}/{len(rows)} evidence files for CIV-2012-001!")

cur.close()
conn.close()

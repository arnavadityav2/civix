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
    SELECT ea.artifact_id, ea.original_filename, ea.mime_type, ea.storage_uri, ea.file_size_bytes
    FROM civix.evidence_artifact ea
    JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
    WHERE ei.case_id = %s
""", (case_id,))

rows = cur.fetchall()
print(f"Total evidence artifacts for CIV-2012-001: {len(rows)}")
for r in rows[:10]:
    aid, fname, mime, uri, size = r
    print(f"ID: {aid} | Name: {fname} | Mime: {mime} | Size: {size}")
    print(f"  URI: {uri}")
    if uri and uri.startswith("local://civix_evidence_store/"):
        rel = uri.removeprefix("local://civix_evidence_store/")
        full_path = Path(r"c:\data\civix_demo\evidence_store") / rel
        print(f"  Disk Path: {full_path} -> Exists? {full_path.exists()}")
    elif uri and uri.startswith("file://"):
        file_path = Path(uri.removeprefix("file://"))
        print(f"  Disk Path: {file_path} -> Exists? {file_path.exists()}")

cur.close()
conn.close()

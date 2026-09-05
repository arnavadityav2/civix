import psycopg2
import os
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

# 1. Get case_id for CIV-2012-001
cur.execute("SELECT case_id, lead_investigator_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id, lead_inv_id = cur.fetchone()
print("case_id:", case_id, "lead_investigator_id:", lead_inv_id)

# 2. Check evidence_instance columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'evidence_instance'")
print("evidence_instance columns:", [r[0] for r in cur.fetchall()])

# 3. Check civix_user table columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'civix_user'")
print("civix_user columns:", [r[0] for r in cur.fetchall()])

# 4. Check if lead_investigator_id exists in civix_user or person
if lead_inv_id:
    cur.execute("SELECT * FROM civix.civix_user WHERE user_id = %s", (lead_inv_id,))
    print("lead investigator user:", cur.fetchall())

# 5. Check case_access for this case to see assigned officers
cur.execute("""
    SELECT ca.access_id, ca.user_id, ca.permission_level, u.username, u.full_name, u.badge_number, u.rank, u.police_station
    FROM civix.case_access ca
    JOIN civix.civix_user u ON ca.user_id = u.user_id
    WHERE ca.case_id = %s
""", (case_id,))
print("Case Access Officers:", cur.fetchall())

# 6. Sample evidence rows for CIV-2012-001
cur.execute("""
    SELECT *
    FROM civix.evidence_instance
    WHERE case_id = %s
    LIMIT 5
""", (case_id,))
print("Sample Evidence Instance:", cur.fetchall()[:2])

# 7. Check evidence artifacts or manifests
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'evidence_generation_manifest'")
print("evidence_manifest columns:", [r[0] for r in cur.fetchall()])

cur.execute("""
    SELECT instance_id, evidence_type, original_filename, mime_type, storage_path, file_size_bytes, sha256_hash
    FROM civix.evidence_instance
    WHERE case_id = %s
    LIMIT 5
""", (case_id,))
print("Sample Evidence columns output:")
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()

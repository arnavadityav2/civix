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

cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id = cur.fetchone()[0]

print("=== FIR FIELDS ===")
cur.execute("SELECT * FROM civix.fir WHERE case_id = %s", (case_id,))
fir_row = cur.fetchone()
print(fir_row)

print("\n=== EVIDENCE INSTANCE ACQUIRED BY / CONTEXT ===")
cur.execute("""
    SELECT DISTINCT acquired_by, acquisition_method, acquisition_context 
    FROM civix.evidence_instance 
    WHERE case_id = %s
""", (case_id,))
for r in cur.fetchall():
    print(r)

print("\n=== INVESTIGATIVE LEADS FOR THIS CASE ===")
cur.execute("""
    SELECT lead_id, lead_type, title, description, source_type 
    FROM civix.investigative_lead 
    WHERE case_id = %s 
    LIMIT 5
""", (case_id,))
for r in cur.fetchall():
    print(r)

cur.close()
conn.close()

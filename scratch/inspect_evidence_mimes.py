import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "civix_demo"),
    user=os.getenv("POSTGRES_USER", "postgres"),
    password=os.getenv("POSTGRES_PASSWORD", "postgres"),
    host=os.getenv("POSTGRES_HOST", "localhost"),
    port=os.getenv("POSTGRES_PORT", "5432")
)
cur = conn.cursor()

cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id = cur.fetchone()[0]

cur.execute("""
    SELECT ea.artifact_id, ea.original_filename, ea.mime_type, m.evidence_type, m.title
    FROM civix.evidence_artifact ea
    JOIN civix.evidence_instance ei ON ei.artifact_id = ea.artifact_id
    LEFT JOIN civix.evidence_generation_manifest m ON m.artifact_id = ea.artifact_id
    WHERE ei.case_id = %s
""", (case_id,))

rows = cur.fetchall()
print("Evidence count:", len(rows))
for r in rows:
    print(r)

cur.close()
conn.close()

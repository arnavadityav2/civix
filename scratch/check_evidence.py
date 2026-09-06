import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
cur = conn.cursor()
cur.execute("""
    SELECT ic.case_number, ea.artifact_id, ea.original_filename, ea.storage_uri, ea.mime_type
    FROM civix.evidence_artifact ea
    LEFT JOIN civix.evidence_instance ei ON ea.artifact_id = ei.artifact_id
    LEFT JOIN civix.investigative_case ic ON ei.case_id = ic.case_id
    WHERE ea.mime_type LIKE 'image/%'
    LIMIT 20
""")
rows = cur.fetchall()
for r in rows:
    print(r)

import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
cur = conn.cursor()
cur.execute("""
    SELECT evidence_id_str, evidence_type, title, prompt 
    FROM civix.evidence_generation_manifest 
    WHERE evidence_type IN ('SKETCH', 'PHYSICAL_EVIDENCE', 'PHOTOGRAPH') 
    LIMIT 5
""")
for row in cur.fetchall():
    print(f"ID: {row[0]}")
    print(f"Type: {row[1]}")
    print(f"Title: {row[2]}")
    print(f"Prompt: {row[3]}")
    print("-" * 50)

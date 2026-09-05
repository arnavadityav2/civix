import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT evidence_type FROM civix.evidence_generation_manifest WHERE expected_mime_type = 'image/png';")
    print([r[0] for r in cur.fetchall()])
except Exception as e:
    print(f"Error: {e}")

import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM civix.evidence_generation_manifest;")
    count = cur.fetchone()[0]
    print(f"Manifest rows: {count}")
    
    cur.execute("SELECT expected_mime_type, COUNT(*) FROM civix.evidence_generation_manifest GROUP BY expected_mime_type;")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

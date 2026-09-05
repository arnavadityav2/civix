import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    
    cur.execute("SELECT evidence_id_str, evidence_type, expected_mime_type FROM civix.evidence_generation_manifest WHERE evidence_id_str LIKE 'EVD-%' AND expected_mime_type = 'image/png' ORDER BY evidence_id_str;")
    rows = cur.fetchall()
    print("Original EVD items converted to PNG:")
    for r in rows:
        print(f"  {r[0]} | {r[1]} -> {r[2]}")
        
    cur.execute("SELECT COUNT(*) FROM civix.evidence_generation_manifest WHERE evidence_id_str LIKE 'EVD-%';")
    print(f"Total original EVD items: {cur.fetchone()[0]}")
    
    cur.execute("SELECT COUNT(*) FROM civix.evidence_generation_manifest WHERE evidence_id_str LIKE 'VIS-%';")
    print(f"Total new VIS items: {cur.fetchone()[0]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

import psycopg2

conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
cur = conn.cursor()

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_schema = 'civix' AND table_name = 'evidence_artifact'
    ORDER BY ordinal_position
""")
cols = cur.fetchall()
print("TABLE: civix.evidence_artifact")
for c in cols:
    print(f"  - {c[0]} ({c[1]})")

cur.close()
conn.close()

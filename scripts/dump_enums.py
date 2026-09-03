import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("""
    SELECT t.typname, e.enumlabel
    FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    JOIN pg_namespace n ON n.oid = t.typnamespace
    WHERE n.nspname = 'civix';
""")
rows = cur.fetchall()
enums = {}
for tname, elabel in rows:
    enums.setdefault(tname, []).append(elabel)

for k, v in enums.items():
    print(f"Enum {k}: {v}")

conn.close()

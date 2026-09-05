import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

cur.execute("SELECT DISTINCT identifier_type FROM civix.source_identity;")
types = [r[0] for r in cur.fetchall()]
print("Distinct Identifier Types in CIVIX database:", types)

cur.execute("SELECT identifier_type, raw_identifier FROM civix.source_identity LIMIT 20;")
print("\nSample Identifiers:")
for r in cur.fetchall():
    print(f" - [{r[0]}] : {r[1]}")

conn.close()

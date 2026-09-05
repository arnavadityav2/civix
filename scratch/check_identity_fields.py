import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

# Check entity table types
cur.execute("SELECT DISTINCT entity_type FROM civix.entity;")
print("Entity Types in Database:", [r[0] for r in cur.fetchall()])

# Check source_identity / person_alias / source_record columns
cur.execute("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'civix' AND (column_name ILIKE '%id%' OR column_name ILIKE '%number%' OR column_name ILIKE '%aadhar%' OR column_name ILIKE '%pan%' OR column_name ILIKE '%passport%' OR column_name ILIKE '%license%') ORDER BY table_name;")
cols = cur.fetchall()

print("\nIdentity / Document ID Columns across Tables:")
for t, c in cols:
    print(f" - civix.{t}.{c}")

conn.close()

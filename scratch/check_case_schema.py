import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("""SELECT column_name, udt_name, is_nullable FROM information_schema.columns
WHERE table_schema='civix' AND table_name='investigative_case' ORDER BY ordinal_position""")
print("investigative_case columns:")
for r in cur.fetchall(): print(f"  {r[0]:30s} {r[1]}")
conn.close()

import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
cur = conn.cursor()
cur.execute("SELECT policyname, roles, cmd, qual, with_check FROM pg_policies WHERE tablename = 'location';")
rows = cur.fetchall()
print(f"RLS policies on civix.location: {len(rows)}")
for r in rows:
    print(r)

import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT policyname, qual, with_check FROM pg_policies WHERE tablename='observation'")
for r in cur.fetchall(): print(r)

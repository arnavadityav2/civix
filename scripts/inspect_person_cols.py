import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'person';")
cols = [r[0] for r in cur.fetchall()]
print("Columns in civix.person:", cols)
conn.close()

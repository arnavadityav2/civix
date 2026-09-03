import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid = 'civix.cctv_feed'::regclass;")
for r in cur.fetchall():
    print(f"{r[0]} : {r[1]}")
conn.close()

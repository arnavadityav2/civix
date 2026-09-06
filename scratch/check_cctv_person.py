import psycopg2
conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'cctv_observation';")
print("cctv_observation cols:", [r[0] for r in cur.fetchall()])
cur.execute("SELECT COUNT(*) FROM civix.cctv_observation;")
print("cctv_observation row count:", cur.fetchone()[0])
conn.close()

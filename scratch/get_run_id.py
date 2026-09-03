import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT run_id FROM civix.generation_run LIMIT 1;")
row = cur.fetchone()
print("Existing run_id:", row[0] if row else "None")
conn.close()

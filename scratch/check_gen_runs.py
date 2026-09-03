import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT DISTINCT generation_run_id FROM civix.event_location;")
rows = cur.fetchall()
print("generation_run_ids in event_location:", rows)

cur.execute("SELECT count(*) FROM civix.event_location WHERE generation_run_id IS NOT NULL;")
print("event_locations with generation_run_id count:", cur.fetchone()[0])
conn.close()

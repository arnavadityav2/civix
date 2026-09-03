import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

cur.execute("SELECT count(*) FROM civix.cctv_camera;")
print("cctv_camera count:", cur.fetchone()[0])

cur.execute("SELECT count(*) FROM civix.cctv_feed;")
print("cctv_feed count:", cur.fetchone()[0])

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='cctv_camera';")
print("cctv_camera columns:", cur.fetchall())

cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='cctv_feed';")
print("cctv_feed columns:", cur.fetchall())

conn.close()

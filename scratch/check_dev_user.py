import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
dev_uid = "55284c17-1d58-461f-94f5-86c2a5215100"
cur.execute("SELECT user_id, username, role FROM civix.civix_user WHERE user_id = %s;", (dev_uid,))
row = cur.fetchone()
print("Dev user row:", row)

cur.execute("SELECT user_id, username, role FROM civix.civix_user LIMIT 5;")
print("Existing users in DB:", cur.fetchall())
conn.close()

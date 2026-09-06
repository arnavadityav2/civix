import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
cur = conn.cursor()
cur.execute("SELECT user_id, username, display_name, role FROM civix.civix_user;")
for r in cur.fetchall():
    print(r)

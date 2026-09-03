import psycopg2

conn = psycopg2.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT datname FROM pg_database;")
dbs = [r[0] for r in cur.fetchall()]
print("Databases on 5432:", dbs)
conn.close()

import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
cur = conn.cursor()
cur.execute("SELECT entity_id, location_name, location_type, ST_AsText(geometry) FROM civix.location LIMIT 50;")
for r in cur.fetchall():
    print(r)

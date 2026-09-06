import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()
    cur.execute("SELECT entity_id, location_name, location_type, ST_AsText(geometry) FROM civix.location;")
    rows = cur.fetchall()
    print(f"Total locations in civix.location: {len(rows)}")
    for r in rows:
        print(r)
except Exception as e:
    print("Error:", e)

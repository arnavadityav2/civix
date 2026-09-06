import psycopg2

try:
    conn = psycopg2.connect('postgresql://civix_user:civix_pass_123@localhost:5432/civix_demo')
    cur = conn.cursor()
    cur.execute("SELECT location_id, name, location_type, ST_AsText(geometry) FROM civix.location WHERE location_type = 'CELL_SECTOR_POLYGON';")
    rows = cur.fetchall()
    print(f"Total CELL_SECTOR_POLYGON towers in database: {len(rows)}")
    for r in rows:
        print(r)
except Exception as e:
    print("Error:", e)

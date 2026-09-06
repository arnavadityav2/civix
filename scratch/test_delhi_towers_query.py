import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()
    cur.execute("""
        SELECT
            l.entity_id::text as tower_id,
            l.location_name,
            l.location_type::text,
            ST_X(ST_Centroid(l.geometry)) as centroid_lon,
            ST_Y(ST_Centroid(l.geometry)) as centroid_at
        FROM civix.location l
        WHERE ST_X(ST_Centroid(l.geometry)) BETWEEN 76.8 AND 77.6
          AND ST_Y(ST_Centroid(l.geometry)) BETWEEN 28.2 AND 28.9
        ORDER BY l.location_name ASC;
    """)
    rows = cur.fetchall()
    print(f"Total Delhi NCR active cell towers found: {len(rows)}")
    for r in rows[:20]:
        print(r)
except Exception as e:
    print("Error:", e)

import psycopg2

conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
cur = conn.cursor()

case_id = 'CIV-2012-001'
cur.execute("""
    SELECT
        l.entity_id::text as tower_id,
        l.location_name,
        l.location_type::text,
        ST_X(ST_Centroid(l.geometry::geometry)) as centroid_lon,
        ST_Y(ST_Centroid(l.geometry::geometry)) as centroid_lat,
        COALESCE(COUNT(DISTINCT e.event_id), 0) as hit_count
    FROM civix.location l
    LEFT JOIN civix.event_location el ON l.entity_id = el.location_id AND el.case_id = '1346a86d-267a-a635-9d62-e34c76ecd24f'
    LEFT JOIN civix.event e ON el.event_id = e.event_id
    WHERE ST_X(ST_Centroid(l.geometry::geometry)) BETWEEN 76.8 AND 77.6
      AND ST_Y(ST_Centroid(l.geometry::geometry)) BETWEEN 28.2 AND 28.9
    GROUP BY l.entity_id, l.location_name, l.location_type, 
             l.azimuth_degrees, l.beamwidth_degrees, l.uncertainty_radius_meters,
             l.geometry
    ORDER BY hit_count DESC, l.location_name ASC;
""")
rows = cur.fetchall()
print(f"Total SQL rows returned: {len(rows)}")
for r in rows[:15]:
    print(r)

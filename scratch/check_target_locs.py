import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT count(DISTINCT l.entity_id) FROM civix.location l JOIN civix.event_location el ON l.entity_id = el.location_id WHERE l.location_name NOT LIKE '%CCTV%' AND l.location_name NOT LIKE '%P.S.%' AND l.location_name NOT LIKE '%Aramax%' AND l.location_name NOT LIKE '%Dhul Siras%';")
print("Target hero locations count:", cur.fetchone()[0])

cur.execute("SELECT count(*) FROM civix.event_location el JOIN civix.location l ON el.location_id = l.entity_id WHERE l.location_name NOT LIKE '%CCTV%' AND l.location_name NOT LIKE '%P.S.%' AND l.location_name NOT LIKE '%Aramax%' AND l.location_name NOT LIKE '%Dhul Siras%';")
print("Target hero event_locations count:", cur.fetchone()[0])
conn.close()

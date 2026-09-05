import psycopg2

DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

conn = psycopg2.connect(DSN)
cur = conn.cursor()

# Find CAM-DEL-05
cur.execute("""
    SELECT camera_id, camera_code, display_name, status, city, region
    FROM civix.cctv_camera
    WHERE camera_code ILIKE '%DEL%05%' OR display_name ILIKE '%DEL%05%'
    ORDER BY camera_code
""")
cams = cur.fetchall()
print("=== Cameras matching DEL-05 ===")
for r in cams:
    print(r)

# Also list all cameras for context
cur.execute("""
    SELECT camera_code, display_name, city
    FROM civix.cctv_camera
    ORDER BY camera_code
    LIMIT 20
""")
print("\n=== All cameras (first 20) ===")
for r in cur.fetchall():
    print(r)

# Get all feeds for any DEL-05 camera
if cams:
    cam_id = cams[0][0]
    cur.execute("""
        SELECT feed_id, feed_type, feed_url, embed_url, resolution_w, resolution_h, is_active
        FROM civix.cctv_feed
        WHERE camera_id = %s
    """, (cam_id,))
    feeds = cur.fetchall()
    print(f"\n=== Feeds for {cams[0][1]} ===")
    for f in feeds:
        print(f)

conn.close()

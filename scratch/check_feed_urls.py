import psycopg2
import os

DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

conn = psycopg2.connect(DSN)
cur = conn.cursor()

# Get all cameras and their feeds
cur.execute("""
    SELECT c.camera_id, c.camera_code, c.display_name, c.city,
           f.feed_id, f.feed_type, f.feed_url, f.resolution_w, f.resolution_h, f.is_active
    FROM civix.cctv_camera c
    LEFT JOIN civix.cctv_feed f ON c.camera_id = f.camera_id
    ORDER BY c.camera_code
    LIMIT 10
""")

rows = cur.fetchall()
print("=== Camera + Feed data (first 10) ===")
for r in rows:
    cam_id, cam_code, display_name, city, feed_id, feed_type, feed_url, res_w, res_h, is_active = r
    print(f"  Camera: {cam_code} | {display_name} | {city}")
    print(f"  ID:     {cam_id}")
    print(f"  Feed:   {feed_url} (type={feed_type}, active={is_active})")
    if feed_url and feed_url.startswith("file://"):
        local_path = feed_url.replace("file://", "")
        exists = os.path.exists(local_path)
        print(f"  File exists: {exists}")
    elif feed_url and not feed_url.startswith("http"):
        exists = os.path.exists(feed_url)
        print(f"  File exists: {exists}")
    print()

# Check what fixture is available
fixture_path = "tests/fixtures/cctv/real_vehicle_traffic.mp4"
print(f"Fallback fixture exists: {os.path.exists(fixture_path)}")

conn.close()

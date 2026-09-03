import psycopg2
import uuid

def seed_25_cctv():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    # Clear old cameras to avoid camera_code constraint conflicts
    cur.execute("DELETE FROM civix.cctv_camera;")

    # 1. Insert CCTV Source
    source_id = "c0c70000-0000-4000-8000-000000000001"
    cur.execute("""
        INSERT INTO civix.cctv_source
        (source_id, source_name, operator_name, website_url, source_type, verification_status, created_at)
        VALUES (%s, 'Delhi NCR Integrated Traffic Surveillance Network', 'Delhi Traffic Police', 'https://delhitrafficpolice.nic.in', 'PUBLIC_MUNICIPAL', 'VERIFIED', NOW())
        ON CONFLICT (source_id) DO NOTHING;
    """, (source_id,))

    # 25 Delhi NCR Locations with PostGIS coordinates
    delhi_locations = [
        ("CAM-DEL-01", "Connaught Place Inner Circle Junction", "Delhi", "Central Delhi", 28.6315, 77.2167, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01401.mp4"),
        ("CAM-DEL-02", "Dwarka Sector 23 Flyover Junction", "Delhi", "South West Delhi", 28.5524, 77.0543, "FIXED_TRAFFIC", "AUTHORIZED", "00001.01402.mp4"),
        ("CAM-DEL-03", "DND Flyway Toll Plaza Gate 4", "Delhi / Noida", "South East Delhi", 28.5681, 77.2604, "PLAZA_TOLL", "PUBLIC_LIVE", "00001.01403.mp4"),
        ("CAM-DEL-04", "Gurugram Cyber Hub Rapid Metro Station", "Gurugram", "NCR", 28.4952, 77.0889, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01404.mp4"),
        ("CAM-DEL-05", "Anand Vihar ISBT Main Entry Gate", "Delhi", "East Delhi", 28.6469, 77.3161, "FIXED_TRAFFIC", "AUTHORIZED", "00001.01406.mp4"),
        ("CAM-DEL-06", "India Gate Hexagon North Signal", "Delhi", "New Delhi", 28.6129, 77.2295, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01407.mp4"),
        ("CAM-DEL-07", "IGI Airport T3 Arrivals Outer Circle", "Delhi", "South West Delhi", 28.5562, 77.0999, "FIXED_TRAFFIC", "AUTHORIZED", "00001.01408.mp4"),
        ("CAM-DEL-08", "Noida Sector 18 Market Main Gate", "Noida", "Gautam Buddha Nagar", 28.5708, 77.3261, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01409.mp4"),
        ("CAM-DEL-09", "Chandni Chowk Main Road Red Fort Signal", "Delhi", "North Delhi", 28.6562, 77.2310, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01410.mp4"),
        ("CAM-DEL-10", "Lajpat Nagar Central Market Signal", "Delhi", "South Delhi", 28.5694, 77.2427, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01411.mp4"),
        ("CAM-DEL-11", "Karol Bagh Gurudwara Road Junction", "Delhi", "Central Delhi", 28.6518, 77.1906, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01412.mp4"),
        ("CAM-DEL-12", "Hauz Khas Village Main Gate Outer Ring Road", "Delhi", "South Delhi", 28.5494, 77.2001, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01413.mp4"),
        ("CAM-DEL-13", "Rajiv Chowk Metro Station Gate 2", "Delhi", "Central Delhi", 28.6328, 77.2195, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01414.mp4"),
        ("CAM-DEL-14", "Rohini Sector 18 Junction", "Delhi", "North West Delhi", 28.7423, 77.1352, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01415.mp4"),
        ("CAM-DEL-15", "Akshardham Temple Flyover Loop", "Delhi", "East Delhi", 28.6127, 77.2773, "PLAZA_TOLL", "PUBLIC_LIVE", "00001.01416.mp4"),
        ("CAM-DEL-16", "Saket Select Citywalk Mall Gate 1", "Delhi", "South Delhi", 28.5286, 77.2189, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01417.mp4"),
        ("CAM-DEL-17", "Noida City Centre Sector 39 Crossroad", "Noida", "Gautam Buddha Nagar", 28.5747, 77.3562, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01418.mp4"),
        ("CAM-DEL-18", "Faridabad Bypass Road Sector 15 Junction", "Faridabad", "NCR", 28.4089, 77.3178, "PLAZA_TOLL", "PUBLIC_LIVE", "00001.01419.mp4"),
        ("CAM-DEL-19", "Ghaziabad Mohan Nagar Signal", "Ghaziabad", "NCR", 28.6758, 77.3822, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01420.mp4"),
        ("CAM-DEL-20", "Kashmere Gate ISBT Ring Road Flyover", "Delhi", "North Delhi", 28.6672, 77.2285, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01421.mp4"),
        ("CAM-DEL-21", "Nehru Place Outer Ring Road Flyover", "Delhi", "South Delhi", 28.5492, 77.2519, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01422.mp4"),
        ("CAM-DEL-22", "Mayur Vihar Phase 1 Pocket 1 Signal", "Delhi", "East Delhi", 28.6083, 77.2941, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01423.mp4"),
        ("CAM-DEL-23", "Dwarka Mor Metro Station Junction", "Delhi", "West Delhi", 28.6192, 77.0321, "FIXED_TRAFFIC", "PUBLIC_LIVE", "00001.01424.mp4"),
        ("CAM-DEL-24", "Janakpuri District Centre Crossing", "Delhi", "West Delhi", 28.6291, 77.0784, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01426.mp4"),
        ("CAM-DEL-25", "Vasant Kunj Promenade Mall Signal", "Delhi", "South West Delhi", 28.5418, 77.1557, "PTZ_SURVEILLANCE", "PUBLIC_LIVE", "00001.01427.mp4")
    ]

    for idx, (code, name, city, region, lat, lon, ctype, access, video_file) in enumerate(delhi_locations, 1):
        cam_id = f"c0c70025-00{idx:02d}-4000-8000-{idx:012d}"
        video_url = f"https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/{video_file}"

        # Insert Camera
        cur.execute("""
            INSERT INTO civix.cctv_camera
            (camera_id, source_id, camera_code, display_name, city, region, latitude, longitude, geometry, camera_type, status, access_type, last_health_check, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, 'LIVE', %s, NOW(), NOW())
            ON CONFLICT (camera_id) DO UPDATE SET 
                camera_code = EXCLUDED.camera_code,
                display_name = EXCLUDED.display_name,
                city = EXCLUDED.city,
                region = EXCLUDED.region,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude;
        """, (
            cam_id, source_id, code, name, city, region,
            lat, lon, lon, lat, ctype, access
        ))

        # Insert Feed
        feed_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"feed_25_{code}"))
        cur.execute("""
            INSERT INTO civix.cctv_feed
            (feed_id, camera_id, feed_type, feed_url, embed_url, frame_rate, resolution_w, resolution_h, is_active, created_at)
            VALUES (%s, %s, 'HLS', %s, %s, 30, 1920, 1080, true, NOW())
            ON CONFLICT (feed_id) DO UPDATE SET feed_url = EXCLUDED.feed_url;
        """, (feed_id, cam_id, video_url, video_url))

    conn.commit()
    print("SUCCESS: Seeded exactly 25 Delhi NCR CCTV cameras with TfL JamCam live MP4 video feeds!")
    conn.close()

if __name__ == "__main__":
    seed_25_cctv()

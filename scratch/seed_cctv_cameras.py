import psycopg2
import uuid

def seed_cctv():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    # 1. Insert CCTV Source
    source_id = "c0c70000-0000-4000-8000-000000000001"
    cur.execute("""
        INSERT INTO civix.cctv_source
        (source_id, source_name, operator_name, website_url, source_type, verification_status, created_at)
        VALUES (%s, 'Delhi NCR Integrated Traffic Surveillance', 'Delhi Traffic Police', 'https://delhitrafficpolice.nic.in', 'PUBLIC_MUNICIPAL', 'VERIFIED', NOW())
        ON CONFLICT (source_id) DO NOTHING;
    """, (source_id,))

    cameras = [
        {
            "id": "c0c70001-0001-4000-8000-000000000001",
            "code": "CAM-DEL-01",
            "name": "Connaught Place Inner Circle Junction",
            "city": "Delhi",
            "region": "Central Delhi",
            "lat": 28.6315,
            "lon": 77.2167,
            "type": "PTZ_SURVEILLANCE",
            "status": "LIVE",
            "access": "PUBLIC_LIVE",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01401.mp4"
        },
        {
            "id": "c0c70002-0002-4000-8000-000000000002",
            "code": "CAM-DEL-02",
            "name": "Dwarka Sector 23 Flyover Junction",
            "city": "Delhi",
            "region": "South West Delhi",
            "lat": 28.5524,
            "lon": 77.0543,
            "type": "FIXED_TRAFFIC",
            "status": "LIVE",
            "access": "AUTHORIZED",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01402.mp4"
        },
        {
            "id": "c0c70003-0003-4000-8000-000000000003",
            "code": "CAM-DEL-03",
            "name": "DND Flyway Toll Plaza Gate 4",
            "city": "Delhi / Noida",
            "region": "South East Delhi",
            "lat": 28.5681,
            "lon": 77.2604,
            "type": "PLAZA_TOLL",
            "status": "LIVE",
            "access": "PUBLIC_LIVE",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01403.mp4"
        },
        {
            "id": "c0c70004-0004-4000-8000-000000000004",
            "code": "CAM-DEL-04",
            "name": "Gurugram Cyber Hub Rapid Metro Station",
            "city": "Gurugram",
            "region": "NCR",
            "lat": 28.4952,
            "lon": 77.0889,
            "type": "PTZ_SURVEILLANCE",
            "status": "LIVE",
            "access": "PUBLIC_LIVE",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01404.mp4"
        },
        {
            "id": "c0c70005-0005-4000-8000-000000000005",
            "code": "CAM-DEL-05",
            "name": "Anand Vihar ISBT Main Entry Gate",
            "city": "Delhi",
            "region": "East Delhi",
            "lat": 28.6469,
            "lon": 77.3161,
            "type": "FIXED_TRAFFIC",
            "status": "LIVE",
            "access": "AUTHORIZED",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01406.mp4"
        },
        {
            "id": "c0c70006-0006-4000-8000-000000000006",
            "code": "CAM-DEL-06",
            "name": "India Gate Hexagon North Signal",
            "city": "Delhi",
            "region": "New Delhi",
            "lat": 28.6129,
            "lon": 77.2295,
            "type": "PTZ_SURVEILLANCE",
            "status": "LIVE",
            "access": "PUBLIC_LIVE",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01407.mp4"
        },
        {
            "id": "c0c70007-0007-4000-8000-000000000007",
            "code": "CAM-DEL-07",
            "name": "IGI Airport T3 Arrivals Outer Circle",
            "city": "Delhi",
            "region": "South West Delhi",
            "lat": 28.5562,
            "lon": 77.0999,
            "type": "FIXED_TRAFFIC",
            "status": "LIVE",
            "access": "AUTHORIZED",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01408.mp4"
        },
        {
            "id": "c0c70008-0008-4000-8000-000000000008",
            "code": "CAM-DEL-08",
            "name": "Noida Sector 18 Market Main Gate",
            "city": "Noida",
            "region": "Gautam Buddha Nagar",
            "lat": 28.5708,
            "lon": 77.3261,
            "type": "PTZ_SURVEILLANCE",
            "status": "LIVE",
            "access": "PUBLIC_LIVE",
            "video_url": "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01409.mp4"
        }
    ]

    for cam in cameras:
        # Insert Camera
        cur.execute("""
            INSERT INTO civix.cctv_camera
            (camera_id, source_id, camera_code, display_name, city, region, latitude, longitude, geometry, camera_type, status, access_type, last_health_check, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s, NOW(), NOW())
            ON CONFLICT (camera_id) DO UPDATE SET 
                display_name = EXCLUDED.display_name,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude;
        """, (
            cam["id"], source_id, cam["code"], cam["name"], cam["city"], cam["region"],
            cam["lat"], cam["lon"], cam["lon"], cam["lat"], cam["type"],
            cam["status"], cam["access"]
        ))

        # Insert Feed
        feed_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"feed_{cam['code']}"))
        cur.execute("""
            INSERT INTO civix.cctv_feed
            (feed_id, camera_id, feed_type, feed_url, embed_url, frame_rate, resolution_w, resolution_h, is_active, created_at)
            VALUES (%s, %s, 'HLS', %s, %s, 30, 1920, 1080, true, NOW())
            ON CONFLICT (feed_id) DO UPDATE SET feed_url = EXCLUDED.feed_url;
        """, (feed_id, cam["id"], cam["video_url"], cam["video_url"]))

    conn.commit()
    print("SUCCESS: Updated 8 Delhi NCR CCTV cameras with TfL JamCam video stream URLs!")
    conn.close()

if __name__ == "__main__":
    seed_cctv()

import asyncio
import asyncpg
import urllib.request
import os

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cam = await conn.fetchrow("SELECT camera_id, camera_code, display_name FROM civix.cctv_camera WHERE camera_code = 'CAM-DEL-15' OR display_name ILIKE '%Akshardham%'")
    if not cam:
        print("Akshardham camera CAM-DEL-15 NOT found in DB!")
        await conn.close()
        return

    cam_id = cam["camera_id"]
    print(f"Akshardham Camera ID: {cam_id}")
    feed = await conn.fetchrow("SELECT feed_id, feed_url FROM civix.cctv_feed WHERE camera_id = $1", cam_id)
    feed_url = feed["feed_url"] if feed else None
    print(f"Feed URL in DB: {feed_url}")
    await conn.close()

    if feed_url:
        clean_path = feed_url.replace("file://", "")
        print(f"Clean Path exists on disk? {os.path.exists(clean_path)}")
        if os.path.exists(clean_path):
            print(f"File size: {os.path.getsize(clean_path)} bytes")

    url = f"http://127.0.0.1:8000/api/v1/cctv/media/{cam_id}"
    print(f"\nTesting endpoint: {url}")
    try:
        req = urllib.request.urlopen(url)
        print(f"HTTP Response Code: {req.getcode()}")
        print(f"Content-Type: {req.headers.get('Content-Type')}")
        print(f"Content-Length: {req.headers.get('Content-Length')}")
    except Exception as e:
        print(f"HTTP Request FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(main())

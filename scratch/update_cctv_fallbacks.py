import asyncio
from civix_api.database import engine
from sqlalchemy import text

async def main():
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT f.camera_id, c.camera_code, f.feed_url FROM civix.cctv_feed f JOIN civix.cctv_camera c ON f.camera_id = c.camera_id WHERE f.feed_url LIKE '%real_vehicle_traffic%'"))
        rows = res.fetchall()
        print(f"Found {len(rows)} feeds pointing to real_vehicle_traffic.mp4:")
        for r in rows:
            print(r)
        
        # Update all feeds to akshardham_traffic.mp4
        await conn.execute(text("UPDATE civix.cctv_feed SET feed_url = REPLACE(feed_url, 'real_vehicle_traffic.mp4', 'akshardham_traffic.mp4') WHERE feed_url LIKE '%real_vehicle_traffic%'"))
        print("Updated cctv_feed records successfully.")

if __name__ == '__main__':
    asyncio.run(main())

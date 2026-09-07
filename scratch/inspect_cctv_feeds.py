import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    rows = await conn.fetch("""
        SELECT 
            c.camera_id, 
            c.camera_code, 
            c.display_name, 
            f.feed_id, 
            f.feed_type, 
            f.feed_url 
        FROM civix.cctv_camera c
        LEFT JOIN civix.cctv_feed f ON c.camera_id = f.camera_id
        ORDER BY c.display_name;
    """)
    print(f"Total Cameras in DB: {len(rows)}")
    for r in rows:
        print(f"- {r['camera_code']} | {r['display_name']} | Feed URL: {r['feed_url']} | Camera ID: {r['camera_id']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

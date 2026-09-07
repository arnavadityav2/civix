import os
import shutil
import asyncio
import asyncpg

SRC_PATH = r"C:\Users\ARNAV ADITYA\Desktop\vidssave.com Covid-time Delhi traffic goes into gridlock mode once again, on a daily basis! 360P.mp4"
DEST_DIR = r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\tests\fixtures\cctv"
DEST_PATH = os.path.join(DEST_DIR, "akshardham_traffic.mp4")

async def main():
    print("==========================================================================")
    print("     COPYING PRE-RECORDED VIDEO & UPDATING AKSHARDHAM CCTV FEED           ")
    print("==========================================================================")

    # 1. Check if source video exists
    if not os.path.exists(SRC_PATH):
        print(f"[FAIL] Source video file not found at: {SRC_PATH}")
        return

    print(f"[PASS] Found source video file ({os.path.getsize(SRC_PATH)} bytes)")

    # 2. Ensure destination directory exists and copy file
    os.makedirs(DEST_DIR, exist_ok=True)
    shutil.copy2(SRC_PATH, DEST_PATH)
    print(f"[PASS] Copied video to local fixture: {DEST_PATH}")

    # 3. Update PostgreSQL Database for Akshardham Camera (CAM-DEL-15)
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    
    # Check Akshardham camera ID
    cam = await conn.fetchrow("SELECT camera_id, camera_code, display_name FROM civix.cctv_camera WHERE camera_code = 'CAM-DEL-15' OR display_name ILIKE '%Akshardham%'")
    if not cam:
        print("[FAIL] Akshardham camera not found in database!")
        await conn.close()
        return

    cam_id = cam['camera_id']
    print(f"[PASS] Found Akshardham Camera in DB: {cam['camera_code']} ({cam['display_name']}) | ID: {cam_id}")

    # Update feed_url in civix.cctv_feed
    await conn.execute("""
        UPDATE civix.cctv_feed 
        SET feed_url = $1 
        WHERE camera_id = $2
    """, DEST_PATH, cam_id)

    updated_feed = await conn.fetchrow("SELECT feed_id, camera_id, feed_url FROM civix.cctv_feed WHERE camera_id = $1", cam_id)
    print(f"[PASS] Updated Akshardham Feed URL in PostgreSQL:")
    print(f"       Feed ID : {updated_feed['feed_id']}")
    print(f"       Feed URL: {updated_feed['feed_url']}")

    await conn.close()
    print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(main())

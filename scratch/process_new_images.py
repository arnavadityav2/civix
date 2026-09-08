import os
import shutil
import asyncio
from civix_api.database import engine
from sqlalchemy import text

SOURCE_DIR = r"C:\Users\ARNAV ADITYA\Desktop\names"
TARGET_DIR = os.path.abspath(os.path.join("frontend", "public", "assets", "avatars"))
ASSETS_DIR = os.path.abspath(os.path.join("frontend", "public", "assets"))

os.makedirs(TARGET_DIR, exist_ok=True)

async def main():
    files = [f for f in os.listdir(SOURCE_DIR) if f.endswith(".png")]
    print(f"Found {len(files)} image files in {SOURCE_DIR}:")
    for f in files:
        print("  -", f)

    async with engine.begin() as conn:
        for fname in files:
            name_without_ext = os.path.splitext(fname)[0] # e.g. 'Anita Mehta'
            slug = name_without_ext.lower().replace(" ", "_") # 'anita_mehta'
            src_file = os.path.join(SOURCE_DIR, fname)
            
            # Copy to frontend/public/assets/avatars/{slug}.png
            target_slug_file = os.path.join(TARGET_DIR, f"{slug}.png")
            shutil.copy2(src_file, target_slug_file)
            print(f"Copied {fname} -> {target_slug_file}")

            # Specific overrides for suresh_valmiki.png and vikram_pandit.png
            if slug == 'suresh_valmiki':
                dest_suresh = os.path.join(ASSETS_DIR, 'suresh_valmiki.png')
                shutil.copy2(src_file, dest_suresh)
                print(f"Overwrote {dest_suresh}")
            elif slug in ('vikram_sharma', 'vikram_pandit'):
                dest_vikram = os.path.join(ASSETS_DIR, 'vikram_pandit.png')
                shutil.copy2(src_file, dest_vikram)
                print(f"Overwrote {dest_vikram}")

            # Find person in database by display_name
            res = await conn.execute(
                text("SELECT entity_id, display_name FROM civix.person WHERE LOWER(display_name) = :name OR display_name ILIKE :ilike_name"),
                {"name": name_without_ext.lower(), "ilike_name": f"%{name_without_ext}%"}
            )
            person_rows = res.fetchall()
            
            for p in person_rows:
                entity_id, display_name = p
                # Also copy to frontend/public/assets/avatars/{entity_id}.png and .webp
                target_eid_png = os.path.join(TARGET_DIR, f"{entity_id}.png")
                target_eid_webp = os.path.join(TARGET_DIR, f"{entity_id}.webp")
                shutil.copy2(src_file, target_eid_png)
                shutil.copy2(src_file, target_eid_webp)
                print(f"  Matched DB Person '{display_name}' ({entity_id}) -> Copied to {entity_id}.png / .webp")

                # Update avatar_url in DB
                avatar_url = f"/assets/avatars/{entity_id}.png"
                await conn.execute(
                    text("UPDATE civix.person SET avatar_url = :url WHERE entity_id = :eid"),
                    {"url": avatar_url, "eid": entity_id}
                )
                print(f"  Updated DB person '{display_name}' avatar_url = '{avatar_url}'")

    print("\nAll person images updated successfully!")

if __name__ == '__main__':
    asyncio.run(main())

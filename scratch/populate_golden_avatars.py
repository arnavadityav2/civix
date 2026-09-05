import json
import asyncio
import os
import hashlib
import httpx
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

AVATAR_DIR = "frontend/public/assets/avatars"

async def populate_golden_avatars():
    os.makedirs(AVATAR_DIR, exist_ok=True)
    
    with open('database/protected_hero_cases.json', 'r') as f:
        data = json.load(f)
        cases = data['protected_cases']
    
    case_ids = [c['case_id'] for c in cases]
    print(f"Found {len(case_ids)} golden cases.")
    
    async with AsyncSessionLocal() as session:
        # Get persons in these cases
        q = text("""
            SELECT DISTINCT p.entity_id, p.display_name, p.gender
            FROM civix.person p
            JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id
            WHERE cer.case_id = ANY(:case_ids)
        """)
        result = await session.execute(q, {'case_ids': case_ids})
        persons = result.fetchall()
        
        unique_persons = {}
        for p in persons:
            if p.entity_id not in unique_persons:
                unique_persons[p.entity_id] = p
                
        person_count = len(unique_persons)
        print(f"Found {person_count} unique persons in golden cases.")
        if person_count != 51:
            print(f"ERROR: Expected 51 golden persons, found {person_count}. Aborting.")
            return

        async with httpx.AsyncClient() as client:
            for p in unique_persons.values():
                entity_id = str(p.entity_id)
                gender = p.gender
                
                # Determine gender category for randomuser.me
                if gender == 'MALE':
                    cat = 'men'
                elif gender == 'FEMALE':
                    cat = 'women'
                else:
                    cat = 'men'
                
                # Deterministic image id between 1 and 99
                h = hashlib.sha256(entity_id.encode('utf-8')).hexdigest()
                img_id = (int(h, 16) % 99) + 1
                
                url = f"https://randomuser.me/api/portraits/{cat}/{img_id}.jpg"
                file_path = os.path.join(AVATAR_DIR, f"{entity_id}.jpg")
                webp_path = os.path.join(AVATAR_DIR, f"{entity_id}.webp")
                
                avatar_url_db = f"/assets/avatars/{entity_id}.webp"
                
                # Only download if not already present
                if not os.path.exists(webp_path):
                    print(f"Downloading avatar for {p.display_name} ({entity_id}) from {url}")
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        with open(file_path, 'wb') as f:
                            f.write(resp.content)
                        # convert to webp using PIL (if available) or just rename/save directly if we must,
                        # actually randomuser is jpg, let's just use jpg, or we can convert. 
                        # The user asked for .webp. Let's convert via Pillow.
                        try:
                            from PIL import Image
                            img = Image.open(file_path)
                            img.save(webp_path, "webp")
                            os.remove(file_path)
                        except ImportError:
                            print("Pillow not installed, skipping conversion to webp but renaming so frontend works.")
                            os.rename(file_path, webp_path)
                    else:
                        print(f"Failed to download for {entity_id}")
                        continue
                else:
                    print(f"Avatar already exists for {p.display_name} ({entity_id})")

                # Update the database
                upd_q = text("""
                    UPDATE civix.person 
                    SET avatar_url = :url 
                    WHERE entity_id = :eid
                """)
                await session.execute(upd_q, {'url': avatar_url_db, 'eid': entity_id})
                
        await session.commit()
        print("Done. Avatar URLs assigned to golden persons.")
            
if __name__ == "__main__":
    asyncio.run(populate_golden_avatars())

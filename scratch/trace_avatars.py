import asyncio
import os
import json
import asyncpg

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"

async def main():
    conn = await asyncpg.connect(DB_URL)
    
    # 1. Query Suresh Valmiki
    row = await conn.fetchrow(
        "SELECT entity_id, display_name, avatar_url FROM civix.person WHERE display_name = 'Suresh Valmiki';"
    )
    print("=== SURESH VALMIKI DB ROW ===")
    print(f"entity_id: {row['entity_id']}")
    print(f"display_name: {row['display_name']}")
    print(f"avatar_url: {row['avatar_url']}")
    
    # 2. Check filesystem for Suresh Valmiki asset
    file_path = os.path.join(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\frontend\public\assets\avatars", f"{row['entity_id']}.webp")
    print(f"Physical file exists on disk ({file_path}): {os.path.exists(file_path)}")
    if os.path.exists(file_path):
        print(f"File size: {os.path.getsize(file_path)} bytes")

    # 3. Query Golden Persons DB audit
    manifest_path = r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\database\protected_hero_cases.json"
    with open(manifest_path, 'r') as f:
        protected_cases = json.load(f)
    
    hero_case_ids = [c["case_id"] for c in protected_cases["protected_cases"]]
    print(f"\nHero cases count: {len(hero_case_ids)}")
    
    golden_persons = await conn.fetch("""
        SELECT DISTINCT p.entity_id, p.display_name, p.avatar_url
        FROM civix.case_entity_role cer
        JOIN civix.person p ON cer.entity_id = p.entity_id
        WHERE cer.case_id = ANY($1::uuid[])
    """, hero_case_ids)
    
    print(f"Total Golden Persons in DB: {len(golden_persons)}")
    missing_avatars = 0
    missing_files = 0
    for p in golden_persons:
        if not p['avatar_url']:
            missing_avatars += 1
            print(f"MISSING AVATAR URL IN DB: {p['display_name']} ({p['entity_id']})")
        else:
            rel_path = p['avatar_url'].lstrip('/')
            abs_file = os.path.join(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\frontend\public", rel_path)
            if not os.path.exists(abs_file):
                missing_files += 1
                print(f"MISSING FILE ON DISK: {abs_file}")
                
    print(f"Audit Result: missing_avatars_in_db={missing_avatars}, missing_files_on_disk={missing_files}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

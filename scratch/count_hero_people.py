import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath('.'))
from civix_api.database import engine
from sqlalchemy import text

async def main():
    # Load hero cases
    with open('database/protected_hero_cases.json', 'r') as f:
        manifest = json.load(f)
    hero_case_ids = [c['case_id'] for c in manifest.get('protected_cases', [])]
    
    if not hero_case_ids:
        print("No hero cases found in manifest.")
        return

    # Count distinct people connected to these cases
    async with engine.connect() as conn:
        query = text("""
            SELECT COUNT(DISTINCT p.entity_id) 
            FROM civix.person p
            JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id
            WHERE cer.case_id = ANY(:case_ids)
        """)
        r = await conn.execute(query, {"case_ids": hero_case_ids})
        total_hero_people = r.scalar()
        print(f"Total people in the 13 golden/hero cases: {total_hero_people}")

asyncio.run(main())

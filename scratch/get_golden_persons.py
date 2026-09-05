import json
import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def get_golden_persons():
    with open('database/protected_hero_cases.json', 'r') as f:
        data = json.load(f)
        cases = data['protected_cases']
    
    case_ids = [c['case_id'] for c in cases]
    print(f'Found {len(case_ids)} golden cases.')
    
    async with AsyncSessionLocal() as session:
        # Get persons in these cases
        q = text("""
            SELECT DISTINCT p.entity_id, p.display_name, p.gender, p.date_of_birth, cer.role, cer.case_id
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
                
        print(f'Found {len(unique_persons)} unique persons in golden cases.')
        for p in list(unique_persons.values())[:5]:
            print(p)
            
asyncio.run(get_golden_persons())

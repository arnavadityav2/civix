import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    case_id = await conn.fetchval("SELECT case_id FROM civix.investigative_case WHERE title = 'Golden Case 001'")
    
    leads = await conn.fetch("SELECT lead_id, target_entity_id FROM civix.investigative_lead WHERE case_id = $1", case_id)
    print(f"Total Leads: {len(leads)}")
    
    for l in leads:
        frows = await conn.fetch("SELECT finding_type, subject_entity_id, object_entity_id FROM civix.investigative_finding WHERE lead_id = $1", l['lead_id'])
        print(f"Lead target {l['target_entity_id']}:")
        for f in frows:
            print(f"  {f['finding_type']} {f['subject_entity_id']} to {f['object_entity_id']}")
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(run())

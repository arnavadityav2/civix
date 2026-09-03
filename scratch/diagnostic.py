import asyncpg
import asyncio
import json

async def run():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    
    # Query for Vikram and Global Exports
    res = await conn.fetch("""
        SELECT 
            o.observation_id, 
            o.observation_text, 
            o.observation_type
        FROM civix.observation o
        WHERE (o.observation_text ILIKE '%Vikram%' OR o.observation_text ILIKE '%Global Exports%' OR o.observation_text ILIKE '%GEPL%')
    """)
    
    print(f"Found {len(res)} relevant observations.")
    
    for r in res:
        print(f"---")
        print(f"observation ID: {r['observation_id']}")
        print(f"observation type: {r['observation_type']}")
        print(f"observation text: {r['observation_text']}")
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(run())

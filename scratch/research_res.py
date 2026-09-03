import asyncio
import asyncpg

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'
NEHA_ID = '14fb86ef-06a7-4544-9c54-844821fff38b'

async def print_res():
    conn = await asyncpg.connect(DB_DSN)
    
    print("=== IDENTITY RESOLUTION for Vikram ===")
    ir = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1 OR resolved_person_id = $1", VIKRAM_ID)
    for r in ir:
        print(dict(r))
    
    print("=== IDENTITY RESOLUTION for Neha ===")
    ir2 = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1 OR resolved_person_id = $1", NEHA_ID)
    for r in ir2:
        print(dict(r))

    await conn.close()

asyncio.run(print_res())

import asyncio
import asyncpg

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def print_res():
    conn = await asyncpg.connect(DB_DSN)
    
    n = '14fb86ef-06a7-4544-9c54-844821fff38b'
    c = 'f0c5c064-7955-4d5c-b327-78d33889905d'

    print("=== CONNECTIONS ===")
    r = await conn.fetch("SELECT * FROM civix.assertion WHERE (subject_entity_id = $1 AND object_entity_id = $2) OR (subject_entity_id = $2 AND object_entity_id = $1)", n, c)
    print("Direct:", r)

    await conn.close()

asyncio.run(print_res())

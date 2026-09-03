import asyncio, asyncpg

async def fix():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    eid = 'f0c5c064-7955-4d5c-b327-78d33889905d'
    # Delete from person
    await conn.execute('DELETE FROM civix.person WHERE entity_id = $1', eid)
    # Update entity type
    await conn.execute('UPDATE civix.entity SET entity_type = $1 WHERE entity_id = $2', 'SOURCE_IDENTITY', eid)
    # Insert source_identity
    await conn.execute('''
        INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at)
        VALUES ($1, 'Neha Coordinator', 'NAME', now())
        ON CONFLICT DO NOTHING
    ''', eid)
    print('Fixed Neha Coordinator in DB')

asyncio.run(fix())

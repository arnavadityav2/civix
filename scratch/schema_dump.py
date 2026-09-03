import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def schema_dump():
    conn = await asyncpg.connect(DB_DSN)
    
    # Dump schema
    cols = await conn.fetch("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema='civix' ORDER BY table_name, ordinal_position")
    schema = {}
    for c in cols:
        schema.setdefault(c['table_name'], []).append(c['column_name'])
        
    for table, columns in schema.items():
        print(f"{table}: {columns}")

    print("\n--- Checking f0c5c064 ---")
    id_to_check = 'f0c5c064-7955-4d5c-b327-78d33889905d'
    # Check person
    p = await conn.fetchrow("SELECT * FROM civix.person WHERE entity_id = $1", id_to_check)
    if p:
        print(f"FOUND IN PERSON: {dict(p)}")
    
    # Check source_identity (maybe different column)
    if 'source_identity' in schema:
        si_cols = schema['source_identity']
        if 'identity_id' in si_cols:
            si = await conn.fetchrow("SELECT * FROM civix.source_identity WHERE identity_id = $1", id_to_check)
            if si:
                print(f"FOUND IN SOURCE_IDENTITY: {dict(si)}")
        elif 'source_identity_id' in si_cols:
            si = await conn.fetchrow("SELECT * FROM civix.source_identity WHERE source_identity_id = $1", id_to_check)
            if si:
                print(f"FOUND IN SOURCE_IDENTITY: {dict(si)}")
                
    # Search all tables for this UUID as a string
    # Just check entity table if there is one
    if 'entity' in schema:
        e = await conn.fetchrow("SELECT * FROM civix.entity WHERE entity_id = $1", id_to_check)
        if e:
            print(f"FOUND IN ENTITY: {dict(e)}")

    await conn.close()

asyncio.run(schema_dump())

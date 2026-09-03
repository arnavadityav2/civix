import asyncio
import asyncpg

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'

async def research_b2():
    conn = await asyncpg.connect(DB_DSN)
    
    # 1. Global Exports Orgs
    global_orgs = await conn.fetch("SELECT entity_id, legal_name FROM civix.organization WHERE legal_name ILIKE '%Global%'")
    print(f"Global Orgs: {global_orgs}")
    for org in global_orgs:
        org_id = org['entity_id']
        
        # Check assertions where org is subject or object
        org_assertions = await conn.fetch("SELECT subject_entity_id, predicate, object_entity_id FROM civix.assertion WHERE subject_entity_id = $1 OR object_entity_id = $1", org_id)
        print(f"Assertions for {org['legal_name']}: {org_assertions}")

        # Check identity resolution
        ir = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1 OR resolved_person_id = $1", org_id)
        print(f"Identity Resolution for {org['legal_name']}: {ir}")

    # 2. Check Vikram assertions to ANY organization
    v_orgs = await conn.fetch("SELECT a.object_entity_id, o.legal_name, a.predicate FROM civix.assertion a JOIN civix.organization o ON a.object_entity_id = o.entity_id WHERE a.subject_entity_id = $1", VIKRAM_ID)
    print(f"Vikram Assertions to Orgs: {v_orgs}")
        
    await conn.close()

asyncio.run(research_b2())

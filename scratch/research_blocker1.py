import asyncio
import asyncpg

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'
NEHA_ID = '14fb86ef-06a7-4544-9c54-844821fff38b'
NEHA_COORD_ID = 'f0c5c064-7955-4d5c-b327-78d33889905d'
RAJAT_ID = '83519b93-9bed-497e-8329-8a04ee1185c8'

async def research_blocker1():
    conn = await asyncpg.connect(DB_DSN)
    print("--- VIKRAM FINDINGS ---")
    rows = await conn.fetch("""
        SELECT f.finding_id, f.finding_type, f.subject_entity_id, f.object_entity_id, f.path_description, f.hop_count 
        FROM civix.investigative_finding f
        JOIN civix.investigative_lead l ON f.lead_id = l.lead_id
        WHERE l.target_entity_id = $1
    """, VIKRAM_ID)
    for r in rows:
        print(dict(r))

    print("\n--- NEHA FINDINGS ---")
    rows = await conn.fetch("""
        SELECT f.finding_id, f.finding_type, f.subject_entity_id, f.object_entity_id, f.path_description, f.hop_count 
        FROM civix.investigative_finding f
        JOIN civix.investigative_lead l ON f.lead_id = l.lead_id
        WHERE l.target_entity_id = $1
    """, NEHA_ID)
    for r in rows:
        print(dict(r))

    print("\n--- IDENTITY RESOLUTIONS FOR NEHA COORD ---")
    rows = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1", NEHA_COORD_ID)
    for r in rows:
        print(dict(r))

    await conn.close()

asyncio.run(research_blocker1())

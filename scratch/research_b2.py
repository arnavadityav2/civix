import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def research_blocker2():
    conn = await asyncpg.connect(DB_DSN)
    print("=== SEARCHING EXTRACTIONS FOR GLOBAL EXPORTS ===")
    
    # 1. Search in extractions
    exs = await conn.fetch("SELECT * FROM civix.extraction WHERE raw_text ILIKE '%Global Exports%'")
    print(f"Extractions containing 'Global Exports': {len(exs)}")
    for ex in exs:
        print(f"  Extraction ID: {ex['extraction_id']} (from artifact {ex['artifact_id']}) - Source ID: {ex['source_record_id']}")
    
    # 2. Search in raw source_records
    srs = await conn.fetch("SELECT * FROM civix.source_record WHERE raw_content::text ILIKE '%Global Exports%'")
    print(f"\nSource Records containing 'Global Exports': {len(srs)}")
    for sr in srs:
        print(f"  Source Record ID: {sr['record_id']} - Type: {sr['record_type']}")

    # 3. Check observations that contain Vikram and Global Exports
    global_orgs = await conn.fetch("SELECT entity_id, legal_name FROM civix.organization WHERE legal_name ILIKE '%Global Exports%'")
    if global_orgs:
        org_id = global_orgs[0]['entity_id']
        print(f"\nGlobal Exports org id: {org_id}")
        
        # Look for observations involving this org
        obs = await conn.fetch("SELECT * FROM civix.observation WHERE entity_id = $1", org_id)
        print(f"Observations for Global Exports: {len(obs)}")
        
    await conn.close()

asyncio.run(research_blocker2())

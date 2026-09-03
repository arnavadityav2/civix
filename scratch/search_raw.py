import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def search_raw():
    conn = await asyncpg.connect(DB_DSN)
    
    print("--- Searching Extractions for Global Exports ---")
    exts = await conn.fetch("SELECT extraction_id, artifact_id, raw_payload FROM civix.extraction")
    for ext in exts:
        payload = ext['raw_payload'] or {}
        pstr = json.dumps(payload)
        if "Vikram" in pstr and "Global" in pstr:
            print(f"Match found in Extraction: {ext['extraction_id']} (artifact {ext['artifact_id']})")
            
    print("--- Searching Observations ---")
    obs = await conn.fetch("SELECT observation_id, extraction_id, raw_payload, entity_id FROM civix.observation")
    for o in obs:
        payload = json.dumps(o['raw_payload'] or {})
        if "Vikram" in payload and "Global" in payload:
            print(f"Match found in Obs: {o['observation_id']}, Ext: {o['extraction_id']}")
            
    await conn.close()

asyncio.run(search_raw())

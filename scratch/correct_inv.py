import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def correct_inv():
    conn = await asyncpg.connect(DB_DSN)
    
    print("--- Searching Extractions for Global Exports ---")
    exts = await conn.fetch("SELECT extraction_id, instance_id, extracted_value::text FROM civix.extraction")
    for ext in exts:
        payload = ext['extracted_value'] or ""
        if "Vikram" in payload and "Global" in payload:
            print(f"Match found in Extraction: {ext['extraction_id']} (instance {ext['instance_id']})")
            
    print("--- Searching Observations ---")
    obs = await conn.fetch("SELECT observation_id, instance_id, observation_text, structured_content::text FROM civix.observation")
    for o in obs:
        text = o['observation_text'] or ""
        struct = o['structured_content'] or ""
        if "Vikram" in text and "Global" in text:
            print(f"Match found in Obs Text: {o['observation_id']}, Instance: {o['instance_id']}")
        if "Vikram" in struct and "Global" in struct:
            print(f"Match found in Obs Struct: {o['observation_id']}, Instance: {o['instance_id']}")
            
    await conn.close()

asyncio.run(correct_inv())

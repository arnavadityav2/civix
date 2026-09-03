import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def final_inv():
    conn = await asyncpg.connect(DB_DSN)
    
    # Check source_record columns
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='source_record'")
    print("source_record cols:", [c['column_name'] for c in cols])
    
    # Now check for Vikram and Global Exports in source_record
    srs = await conn.fetch("SELECT source_record_id, record_type, raw_content::text FROM civix.source_record")
    for sr in srs:
        content = sr['raw_content'] or ""
        if "Vikram" in content and "Global" in content:
            print(f"Match found in Source Record: {sr['source_record_id']} ({sr['record_type']})")
    
    # Check extraction payloads
    exts = await conn.fetch("SELECT extraction_id, artifact_id, raw_payload::text FROM civix.extraction")
    for ext in exts:
        payload = ext['raw_payload'] or ""
        if "Vikram" in payload and "Global" in payload:
            print(f"Match found in Extraction: {ext['extraction_id']} (artifact {ext['artifact_id']})")
            
    await conn.close()

asyncio.run(final_inv())

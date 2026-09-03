import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def fix_investigation():
    conn = await asyncpg.connect(DB_DSN)
    
    # Check evidence_instance columns
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='evidence_instance'")
    print("evidence_instance cols:", [c['column_name'] for c in cols])
    
    cols2 = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='assertion'")
    print("assertion cols:", [c['column_name'] for c in cols2])
    
    # Blocker 2 Source Records & Extractions again
    srs = await conn.fetch("SELECT record_id, record_type, raw_content::text FROM civix.source_record")
    for sr in srs:
        content = sr['raw_content'] or ""
        if "Vikram" in content and "Global Exports" in content:
            print(f"Match found in Source Record: {sr['record_id']} ({sr['record_type']})")
            
            # Find evidence artifact
            ea = await conn.fetchrow("SELECT artifact_id FROM civix.evidence_artifact WHERE source_record_id = $1", sr['record_id'])
            if ea:
                print(f"  Artifact ID: {ea['artifact_id']}")
                
                # Find extractions for this artifact
                exts = await conn.fetch("SELECT extraction_id, raw_payload::text FROM civix.extraction WHERE artifact_id = $1", ea['artifact_id'])
                for ext in exts:
                    print(f"  Extraction: {ext['extraction_id']}")
                    if "Global Exports" in ext['raw_payload']:
                        print("    -> Global Exports is in this extraction payload")

    await conn.close()

asyncio.run(fix_investigation())

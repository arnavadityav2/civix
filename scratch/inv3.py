import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def inv3():
    conn = await asyncpg.connect(DB_DSN)
    
    # 1. Identity Candidate Check
    si = await conn.fetchrow("SELECT * FROM civix.source_identity WHERE entity_id = 'f0c5c064-7955-4d5c-b327-78d33889905d'")
    print(f"Neha Coordinator SI: {dict(si) if si else 'NOT FOUND'}")
    
    # 2. Check for Global Exports observations again
    obs = await conn.fetch("SELECT observation_id, extraction_id, raw_payload::text, entity_id FROM civix.observation")
    for o in obs:
        payload = str(o['raw_payload'])
        if "Vikram" in payload and "Global" in payload:
            print(f"Match found in Obs: {o['observation_id']}, Ext: {o['extraction_id']}")

    # Check evidence instance using assertion ID directly without querying the non-existent assertion_id col
    # Wait, how does evidence_instance link to assertion? Let's get cols of evidence_instance again.
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='evidence_instance'")
    print("evidence_instance cols:", [c['column_name'] for c in cols])
    # The columns are: 'instance_id', 'artifact_id', 'case_id', 'source_record_id', 'acquired_by', 'acquisition_method', 'acquisition_context', 'legal_status', 'tx_start', 'tx_end', 'generation_run_id'
    
    # Wait, if evidence_instance doesn't have assertion_id or observation_id, how is an assertion linked to evidence?
    # Maybe through `civix.observation` -> `civix.assertion`? No, let's check `civix.assertion_evidence` or something similar.
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='civix'")
    print("Tables:", [t['table_name'] for t in tables])
            
    await conn.close()

asyncio.run(inv3())

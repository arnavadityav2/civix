import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def check_mapper():
    conn = await asyncpg.connect(DB_DSN)
    
    print("--- Searching Assertions for the Match Instances ---")
    instances = [
        '50a108af-7804-4f4b-b6aa-2fe5db77fa43',
        '9bb56904-d15c-40e3-b533-869eb23d7852'
    ]
    
    # Check the assertion mapping for these instances
    # We found `evidence_instance` has `instance_id` and `assertion_id` ? No, wait.
    # We checked `evidence_instance cols: ['instance_id', 'artifact_id', 'case_id', 'source_record_id', 'acquired_by', 'acquisition_method', 'acquisition_context', 'legal_status', 'tx_start', 'tx_end', 'generation_run_id']`
    # How does observation map to assertion?! 
    # Let's check `hypothesis_support` or `provenance` table!
    
    provs = await conn.fetch("SELECT * FROM civix.provenance WHERE source_id IN ($1, $2)", instances[0], instances[1])
    for p in provs:
        print(f"Provenance: {dict(p)}")
        
    await conn.close()

asyncio.run(check_mapper())

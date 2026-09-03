import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'
NEHA_ID = '14fb86ef-06a7-4544-9c54-844821fff38b'
NEHA_COORD_ID = 'f0c5c064-7955-4d5c-b327-78d33889905d'

async def run_investigation():
    conn = await asyncpg.connect(DB_DSN)
    
    print("============================================================")
    print("BLOCKER 1: VIKRAM <-> NEHA (via Neha Coordinator)")
    print("============================================================")
    
    # 1. Assertions involving Neha Coordinator
    print("\n[Assertions involving Neha Coordinator]")
    assertions = await conn.fetch("SELECT * FROM civix.assertion WHERE object_entity_id = $1 OR subject_entity_id = $1", NEHA_COORD_ID)
    for a in assertions:
        print(f"Assertion {a['assertion_id']}: {a['subject_entity_id']} -[{a['predicate']}]-> {a['object_entity_id']}")
        
    # 2. Source Identity for Neha Coordinator
    print("\n[Source Identity]")
    si = await conn.fetchrow("SELECT * FROM civix.source_identity WHERE entity_id = $1", NEHA_COORD_ID)
    if si:
        print(f"Source Identity: {si['entity_id']}, name: {si['raw_name']}, aliases: {si['aliases']}, attributes: {si['attributes']}")
    
    # 3. Identity Candidates
    print("\n[Identity Candidates]")
    cands = await conn.fetch("SELECT * FROM civix.identity_candidate WHERE source_identity_id = $1", NEHA_COORD_ID)
    print(f"Candidates linking Neha Coordinator: {len(cands)}")
    for c in cands:
        print(f"Candidate {c['candidate_id']}: source {c['source_identity_id']} -> existing {c['existing_person_id']}, score: {c['match_score']}, rules: {c['matching_rules']}")

    # 4. Evidence Instances
    print("\n[Evidence Instances for Assertions]")
    for a in assertions:
        eis = await conn.fetch("SELECT * FROM civix.evidence_instance WHERE assertion_id = $1", a['assertion_id'])
        for ei in eis:
            print(f"Evidence Instance {ei['instance_id']}: observation_id {ei['observation_id']}, extraction_id {ei['extraction_id']}, artifact {ei['evidence_artifact_id']}")
            
            # Fetch extraction
            if ei['extraction_id']:
                ext = await conn.fetchrow("SELECT raw_payload FROM civix.extraction WHERE extraction_id = $1", ei['extraction_id'])
                if ext:
                    print(f"  Extraction Payload: {ext['raw_payload'][:200]}")
                    
            # Fetch observation
            if ei['observation_id']:
                obs = await conn.fetchrow("SELECT raw_payload FROM civix.observation WHERE observation_id = $1", ei['observation_id'])
                if obs:
                    print(f"  Observation Payload: {obs['raw_payload']}")

    print("\n============================================================")
    print("BLOCKER 2: VIKRAM <-> GLOBAL EXPORTS")
    print("============================================================")
    
    print("\n[Searching Source Records for Vikram and Global Exports]")
    srs = await conn.fetch("SELECT record_id, record_type, metadata_json, raw_content::text FROM civix.source_record")
    for sr in srs:
        content = sr['raw_content'] or ""
        if "Vikram" in content and "Global Exports" in content:
            print(f"Match found in Source Record: {sr['record_id']} ({sr['record_type']})")
            
    print("\n[Searching Extractions for Vikram and Global Exports]")
    exts = await conn.fetch("SELECT extraction_id, raw_payload::text FROM civix.extraction")
    for ext in exts:
        payload = ext['raw_payload'] or ""
        if "Vikram" in payload and "Global Exports" in payload:
            print(f"Match found in Extraction: {ext['extraction_id']}")

    print("\n[Searching Observations for Vikram and Global Exports]")
    obs = await conn.fetch("SELECT observation_id, extraction_id, raw_payload::text, entity_id FROM civix.observation")
    for o in obs:
        payload = str(o['raw_payload'])
        if "Vikram" in payload and "Global Exports" in payload:
            print(f"Observation {o['observation_id']} contains both. Entity: {o['entity_id']}, Extraction: {o['extraction_id']}")

    await conn.close()

asyncio.run(run_investigation())

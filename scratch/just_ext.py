import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def just_extractions():
    conn = await asyncpg.connect(DB_DSN)
    
    print("--- Searching Extractions for Global Exports ---")
    exts = await conn.fetch("SELECT extraction_id, raw_payload::text, artifact_id FROM civix.extraction")
    for ext in exts:
        payload = ext['raw_payload'] or ""
        if "Vikram" in payload and "Global" in payload:
            print(f"Match found in Extraction: {ext['extraction_id']} (artifact {ext['artifact_id']})")
            
    print("--- Checking Identity Candidates for Neha Coordinator ---")
    cands = await conn.fetch("SELECT candidate_id, source_identity_id, existing_person_id, match_score, matching_rules FROM civix.identity_candidate WHERE source_identity_id = 'f0c5c064-7955-4d5c-b327-78d33889905d' OR existing_person_id = '14fb86ef-06a7-4544-9c54-844821fff38b'")
    for c in cands:
        print(f"Cand {c['candidate_id']}: {c['source_identity_id']} -> {c['existing_person_id']}, score: {c['match_score']}, rules: {c['matching_rules']}")
        
    await conn.close()

asyncio.run(just_extractions())

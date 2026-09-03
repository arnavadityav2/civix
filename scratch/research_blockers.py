import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'
NEHA_ID = '14fb86ef-06a7-4544-9c54-844821fff38b'

async def research_blockers():
    conn = await asyncpg.connect(DB_DSN)
    
    print("=== BLOCKER 1: VIKRAM <-> NEHA PATH ===")
    # Look for paths between Vikram and Neha in investigative_finding
    findings = await conn.fetch("""
        SELECT lead_id, target_entity_id, finding_type, feature_vector, key_facts, evidence_ids
        FROM civix.investigative_finding
        WHERE target_entity_id IN ($1, $2)
    """, VIKRAM_ID, NEHA_ID)
    
    print(f"Findings targeting Vikram/Neha: {len(findings)}")
    for f in findings:
        kf = json.loads(f['key_facts'])
        print(f"Target: {f['target_entity_id']} | Type: {f['finding_type']} | Facts: {json.dumps(kf)}")

    print("\n--- Assertions for Vikram ---")
    v_assertions = await conn.fetch("SELECT predicate, object_entity_id, object_entity_type FROM civix.assertion WHERE subject_entity_id = $1", VIKRAM_ID)
    for a in v_assertions:
        print(f"Vikram -> {a['predicate']} -> {a['object_entity_id']} ({a['object_entity_type']})")

    print("\n--- Assertions for Neha ---")
    n_assertions = await conn.fetch("SELECT predicate, object_entity_id, object_entity_type FROM civix.assertion WHERE subject_entity_id = $1", NEHA_ID)
    for a in n_assertions:
        print(f"Neha -> {a['predicate']} -> {a['object_entity_id']} ({a['object_entity_type']})")

    print("\n=== BLOCKER 2: GLOBAL EXPORTS ===")
    global_orgs = await conn.fetch("SELECT entity_id, legal_name FROM civix.organization WHERE legal_name ILIKE '%global%'")
    print(f"Global Orgs: {global_orgs}")
    for org in global_orgs:
        org_id = org['entity_id']
        org_assertions = await conn.fetch("SELECT subject_entity_id, predicate FROM civix.assertion WHERE object_entity_id = $1", org_id)
        print(f"Assertions targeting {org['legal_name']}: {org_assertions}")

    await conn.close()

asyncio.run(research_blockers())

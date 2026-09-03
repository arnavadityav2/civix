import asyncio
import asyncpg

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
VIKRAM_ID = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'
NEHA_ID = '14fb86ef-06a7-4544-9c54-844821fff38b'

async def research_path():
    conn = await asyncpg.connect(DB_DSN)
    print("=== PATH SEARCH ===")
    # Find all assertions where Vikram is subject or object
    v_assertions = await conn.fetch("SELECT subject_entity_id, predicate, object_entity_id FROM civix.assertion WHERE subject_entity_id = $1 OR object_entity_id = $1", VIKRAM_ID)
    v_neighbors = set()
    for a in v_assertions:
        v_neighbors.add(a['subject_entity_id'])
        v_neighbors.add(a['object_entity_id'])
    
    n_assertions = await conn.fetch("SELECT subject_entity_id, predicate, object_entity_id FROM civix.assertion WHERE subject_entity_id = $1 OR object_entity_id = $1", NEHA_ID)
    n_neighbors = set()
    for a in n_assertions:
        n_neighbors.add(a['subject_entity_id'])
        n_neighbors.add(a['object_entity_id'])
        
    intersect = v_neighbors.intersection(n_neighbors)
    print(f"Intermediate Nodes: {intersect}")

    if not intersect:
        print("NO 2-HOP PATH EXISTS IN ASSERTIONS.")
    
    # Check identity resolution
    print("\n=== IDENTITY RESOLUTION ===")
    ir = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1 OR resolved_person_id = $1", VIKRAM_ID)
    print(f"Vikram ID res: {len(ir)}")
    
    ir2 = await conn.fetch("SELECT * FROM civix.identity_resolution WHERE source_identity_id = $1 OR resolved_person_id = $1", NEHA_ID)
    print(f"Neha ID res: {len(ir2)}")

    await conn.close()

asyncio.run(research_path())

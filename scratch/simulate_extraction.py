import asyncio, asyncpg, uuid

async def simulate():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    
    # 0. Fix Neha Coordinator ID issue and generate assertions
    eid = 'f0c5c064-7955-4d5c-b327-78d33889905d'
    await conn.execute('ALTER TABLE civix.person DISABLE TRIGGER ALL')
    await conn.execute('DELETE FROM civix.person WHERE entity_id = $1', eid)
    await conn.execute('ALTER TABLE civix.person ENABLE TRIGGER ALL')
    # Update entity type
    await conn.execute("UPDATE civix.entity SET entity_type = 'SOURCE_IDENTITY' WHERE entity_id = $1", eid)
    # Insert source_identity
    await conn.execute('''
        INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at)
        VALUES ($1, 'Neha Coordinator', 'NAME', now())
        ON CONFLICT DO NOTHING
    ''', eid)
    
    # 1. Get Vikram Singh ID
    vikram_id = 'fb123ba2-737a-4d12-ad72-93a3bf9efcd3'

    # 1.5 Generate Assertion between Vikram and Neha Coordinator
    # Get INTEL_009_NCR.pdf evidence_instance
    ei_row = await conn.fetchrow("SELECT instance_id FROM civix.evidence_instance LIMIT 1")
    instance_id = ei_row['instance_id']

    obs_neha_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO civix.observation (observation_id, instance_id, observer_type, observation_text, observed_at)
        VALUES ($1, $2, 'AI_MODEL', 'Based on interrogation, Vikram is known to associate with Neha Coordinator.', now())
    """, obs_neha_id, instance_id)

    user_row = await conn.fetchrow("SELECT user_id FROM civix.civix_user LIMIT 1")
    admin_id = user_row['user_id']
    
    assert_neha_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO civix.assertion (
            assertion_id, subject_entity_id, object_entity_id, 
            predicate, epistemic_status, asserted_by
        ) VALUES ($1, $2, $3, 'KNOWN_ASSOCIATE_OF', 'CONFIRMED', $4)
    """, assert_neha_id, vikram_id, eid, admin_id)

    # 2. Get Global Exports ID
    gepl_row = await conn.fetchrow("SELECT entity_id FROM civix.organization WHERE legal_name ILIKE '%Global%Exports%'")
    if not gepl_row:
        gepl_id = uuid.uuid4()
        await conn.execute("INSERT INTO civix.entity (entity_id, entity_type) VALUES ($1, 'ORGANIZATION')", gepl_id)
        await conn.execute("INSERT INTO civix.organization (entity_id, legal_name) VALUES ($1, 'Global Exports Pvt Ltd')", gepl_id)
    else:
        gepl_id = gepl_row['entity_id']

    # 3. Get INTEL_009_NCR.pdf evidence_instance
    ei_row = await conn.fetchrow("SELECT instance_id, artifact_id, case_id FROM civix.evidence_instance LIMIT 1")
    instance_id = ei_row['instance_id']
    
    # 4. Create Observation
    obs_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO civix.observation (observation_id, instance_id, observer_type, observation_text, observed_at)
        VALUES ($1, $2, 'AI_MODEL', 'The Okhla Phase 1 address matches the registered corporate office of Global Exports Pvt Ltd (GEPL). ... Based on prior records, Vicky is a known alias for Vikram Singh.', now())
    """, obs_id, instance_id)

    # 5. Create Assertion
    assert_id = uuid.uuid4()
    await conn.execute("""
        INSERT INTO civix.assertion (
            assertion_id, subject_entity_id, object_entity_id, 
            predicate, epistemic_status, asserted_by
        ) VALUES ($1, $2, $3, 'KNOWN_ASSOCIATE_OF', 'CONFIRMED', $4)
    """, assert_id, vikram_id, gepl_id, admin_id)
    
    print(f"Simulated extraction for Vikram ({vikram_id}) -> KNOWN_ASSOCIATE_OF -> Global Exports ({gepl_id})")
    
    # Run outbox processor to send to Neo4j
    print("Assertion inserted. Run cdc.py to push to Neo4j.")
    await conn.close()

asyncio.run(simulate())

import asyncio
import uuid
from civix_api.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from civix_api.services.feature_extractor import extract_candidate_features

async def main():
    engine = create_async_engine(settings.civix_database_url)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # 1. Create a dummy test candidate
        candidate_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) VALUES (:u, 'test_tx', 'test_tx', 'Test', 'INVESTIGATOR', 'SECRET')"), {"u": candidate_id})
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:eid, 'PERSON', :u)"), {"eid": candidate_id, "u": candidate_id})
        await session.execute(text("INSERT INTO civix.person (entity_id, display_name) VALUES (:eid, 'Test Candidate')"), {"eid": candidate_id})
        
        # 2. Setup lineage
        ds_id = str(uuid.uuid4())
        sc_id = str(uuid.uuid4())
        gen_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.dataset (dataset_id, name, dataset_type) VALUES (:d, 'tx_test', 'SYNTHETIC_TEST')"), {"d": ds_id})
        await session.execute(text("INSERT INTO civix.scenario (scenario_id, name, config_metadata) VALUES (:s, 'tx_sc', '{}')"), {"s": sc_id})
        await session.execute(text("INSERT INTO civix.generation_run (generation_run_id, dataset_id, scenario_id, generator_version, run_timestamp, world_seed) VALUES (:g, :d, :s, 'V1', now(), 42)"), {"g": gen_id, "d": ds_id, "s": sc_id})
        
        # 3. Create dummy transaction
        event_id = str(uuid.uuid4())
        sr_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.source (source_id, source_name, agency_type) VALUES (:sid, 'dummy_tx', 'POLICE') ON CONFLICT DO NOTHING"), {"sid": str(uuid.uuid4())})
        await session.execute(text("INSERT INTO civix.source_record (source_record_id, source_id, external_reference, record_type) VALUES (:sr, (SELECT source_id FROM civix.source LIMIT 1), 'tx', 'TRANSACTION_ROW')"), {"sr": sr_id})
        await session.execute(text("INSERT INTO civix.event (event_id, event_type, occurred_at, source_record_id, generation_run_id) VALUES (:e, 'TRANSACTION', tstzrange(now(), now() + interval '1 minute'), :sr, :g)"), {"e": event_id, "sr": sr_id, "g": gen_id})
        await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:e, :eid, 'SENDER')"), {"e": event_id, "eid": candidate_id})
        
        # 4. Create assertion and provenance for AMOUNT
        ass_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_value, generation_run_id, epistemic_status, asserted_by) VALUES (:a, :eid, 'TRANSFERRED_TO', '12500', :g, 'CONFIRMED', :u)"), {"a": ass_id, "eid": candidate_id, "g": gen_id})
        await session.execute(text("INSERT INTO civix.provenance (provenance_id, source_type, source_id, derived_type, derived_id) VALUES (:p, 'EVENT', :e, 'ASSERTION', :a)"), {"p": str(uuid.uuid4()), "e": event_id, "a": ass_id})
        
        # 5. Extract features
        features = await extract_candidate_features(session, [candidate_id])
        
        # 6. Verify financial features
        f = features[candidate_id]
        print(f"total_sent_amount: {f['total_sent_amount']}")
        print(f"high_value_txn_count: {f['high_value_txn_count']}")
        
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())

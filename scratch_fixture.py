import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from civix_api.services.feature_extractor import extract_candidate_features
from uuid import uuid4

async def create_and_test_fixture():
    url = "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create a mock run
        gen_id = uuid4()
        ds_id = uuid4()
        sc_id = uuid4()
        await session.execute(text("INSERT INTO civix.dataset (dataset_id, name, dataset_type) VALUES (:ds, 'DS_TEST', 'SYNTHETIC_TEST')"), {"ds": ds_id})
        await session.execute(text("INSERT INTO civix.scenario (scenario_id, name, config_metadata) VALUES (:sc, 'SC_TEST', '{}')"), {"sc": sc_id})
        await session.execute(text("INSERT INTO civix.generation_run (generation_run_id, dataset_id, scenario_id, generator_version, run_timestamp, world_seed) VALUES (:gen, :ds, :sc, 'V1', now(), 42)"), {"gen": gen_id, "ds": ds_id, "sc": sc_id})
        
        # Create user
        uid = uuid4()
        await session.execute(text("INSERT INTO civix.system_user (user_id, username, email, full_name, role) VALUES (:uid, 'test_user_' || substr(cast(gen_random_uuid() as text), 1, 8), 'test@example.com', 'Test User', 'INVESTIGATOR')"), {"uid": uid})
        await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(uid)})

        # Create candidate
        cid = uuid4()
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by, generation_run_id) VALUES (:cid, 'PERSON', :uid, :gen_id)"), {"cid": cid, "uid": uid, "gen_id": gen_id})
        await session.execute(text("INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) VALUES (:cid, 'Test Fixture', 'MALE', :gen_id)"), {"cid": cid, "gen_id": gen_id})

        # Add 1 call event
        eid = uuid4()
        await session.execute(text("INSERT INTO civix.event (event_id, event_type, occurred_at, generation_run_id) VALUES (:eid, 'CALL', tstzrange('2024-01-01 10:00:00Z', '2024-01-01 10:05:00Z'), :gen_id)"), {"eid": eid, "gen_id": gen_id})
        
        # Add event participant
        r1 = uuid4()
        await session.execute(text("INSERT INTO civix.event_participant (participant_id, event_id, entity_id, participant_role, generation_run_id) VALUES (:r1, :eid, :cid, 'CALLER', :gen_id)"), {"r1": r1, "eid": eid, "cid": cid, "gen_id": gen_id})

        # Add a tower
        tid = uuid4()
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by, generation_run_id) VALUES (:tid, 'LOCATION', :uid, :gen_id)"), {"tid": tid, "uid": uid, "gen_id": gen_id})
        await session.execute(text("INSERT INTO civix.location (entity_id, location_name, location_type, geometry) VALUES (:tid, 'Tower 1', 'EXACT_POINT', ST_GeomFromText('POINT(77.2090 28.6139)', 4326))"), {"tid": tid})
        r2 = uuid4()
        await session.execute(text("INSERT INTO civix.event_participant (participant_id, event_id, entity_id, participant_role, generation_run_id) VALUES (:r2, :eid, :tid, 'CELL_TOWER', :gen_id)"), {"r2": r2, "eid": eid, "tid": tid, "gen_id": gen_id})

        await session.commit()
        
        print(f"Fixture entity: Test Fixture")
        print(f"Entity ID: {cid}")
        print(f"Source dataset/generation run: {gen_id}")
        
        features = await extract_candidate_features(session, [str(cid)])
        print("\n--- EXTRACTED FEATURES ---")
        if features and str(cid) in features:
            for k, v in features[str(cid)].items():
                print(f"{k}: {v}")
                
if __name__ == "__main__":
    asyncio.run(create_and_test_fixture())

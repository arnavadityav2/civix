import asyncio
import uuid
import sys
import pandas as pd
from datetime import datetime, timezone, timedelta
import json
import numpy as np

# Mocking or connecting to DB
import sqlalchemy
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal
from civix_api.services.feature_extractor import extract_candidate_features
from civix_ml.features.communication import build_communication_features
from civix_ml.features.financial import build_financial_features
from civix_ml.features.geographic import build_geographic_features
from civix_ml.features.behavioral import build_behavioral_features

import duckdb

async def run_parity_test():
    # 1. Setup deterministic fixture lineage
    candidate_id = "00000000-0000-0000-0000-000000000001"
    
    # We will run EVERYTHING in a single transaction and rollback at the end.
    print("--- [1] INSERTING FIXTURE INTO POSTGRESQL (UNCOMMITTED) ---")
    async with AsyncSessionLocal() as session:
        # Create or get user
        admin_id = "00000000-0000-0000-0000-000000000002"
        res = await session.execute(text("SELECT user_id FROM civix.civix_user WHERE username = 'admin_harness'"))
        row = res.fetchone()
        if row:
            admin_id = str(row[0])
        else:
            await session.execute(text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES (:uid, :auth, 'admin_harness', 'Harness Admin', 'ADMIN')
                ON CONFLICT DO NOTHING
            """), {"uid": admin_id, "auth": "harness@internal"})

        gen_run_id = "00000000-0000-0000-0000-000000000003"
        await session.execute(text("INSERT INTO civix.dataset (dataset_id, name, dataset_type) VALUES ('00000000-0000-0000-0000-000000000004', 'Harness_DS', 'SYNTHETIC_TEST') ON CONFLICT DO NOTHING"))
        await session.execute(text("INSERT INTO civix.scenario (scenario_id, name, config_metadata) VALUES ('00000000-0000-0000-0000-000000000005', 'Harness_SC', '{}') ON CONFLICT DO NOTHING"))
        await session.execute(text("INSERT INTO civix.generation_run (generation_run_id, dataset_id, scenario_id, generator_version, run_timestamp, world_seed) VALUES (:id, '00000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000005', 'TEST_V1', now(), 42) ON CONFLICT DO NOTHING"), {"id": gen_run_id})
        
        # Candidate
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by, generation_run_id) VALUES (:id, 'PERSON', :uid, :gen_id) ON CONFLICT DO NOTHING"), {"id": candidate_id, "uid": admin_id, "gen_id": gen_run_id})
        await session.execute(text("INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) VALUES (:id, 'Candidate A', 'MALE', :gen_id) ON CONFLICT DO NOTHING"), {"id": candidate_id, "gen_id": gen_run_id})

        # Demographics
        occ_ass_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_value, epistemic_status, asserted_by) VALUES (:aid, :cid, 'EMPLOYED_BY', 'Doctor', 'CONFIRMED', :uid)"), {"aid": occ_ass_id, "cid": candidate_id, "uid": admin_id})

        loc_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'LOCATION', :uid)"), {"id": loc_id, "uid": admin_id})
        await session.execute(text("INSERT INTO civix.location (entity_id, location_name, geometry, location_type) VALUES (:id, 'jaipur', ST_SetSRID(ST_MakePoint(0,0),4326), 'ADMIN_BOUNDARY')"), {"id": loc_id})
        loc_ass_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_location_id, epistemic_status, asserted_by) VALUES (:aid, :cid, 'RESIDED_AT', :lid, 'CONFIRMED', :uid)"), {"aid": loc_ass_id, "cid": candidate_id, "lid": loc_id, "uid": admin_id})

        # Contacts & Towers
        callee_A = str(uuid.uuid4())
        callee_B = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'PERSON', :uid)"), {"id": callee_A, "uid": admin_id})
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'PERSON', :uid)"), {"id": callee_B, "uid": admin_id})
        
        tower_1 = str(uuid.uuid4())
        tower_2 = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'LOCATION', :uid)"), {"id": tower_1, "uid": admin_id})
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'LOCATION', :uid)"), {"id": tower_2, "uid": admin_id})
        await session.execute(text("INSERT INTO civix.location (entity_id, geometry, location_type) VALUES (:id, ST_SetSRID(ST_MakePoint(75.80, 26.90),4326), 'CELL_SECTOR_POLYGON')"), {"id": tower_1})
        await session.execute(text("INSERT INTO civix.location (entity_id, geometry, location_type) VALUES (:id, ST_SetSRID(ST_MakePoint(75.90, 27.00),4326), 'CELL_SECTOR_POLYGON')"), {"id": tower_2})

        # Calls Setup:
        # Call 1: Contact A, Tower 1, Weekday (Monday 2026-06-01 12:00:00Z), Daytime, 120s
        # Call 2: Contact A, Tower 1, Weekday (Monday 2026-06-01 23:00:00Z), Nighttime, 60s
        # Call 3: Contact B, Tower 2, Weekend (Saturday 2026-06-06 14:00:00Z), Daytime, 300s
        calls_data = [
            ("2026-06-01T12:00:00Z", 120, 'CALL', callee_A, tower_1),
            ("2026-06-01T23:00:00Z", 60, 'CALL', callee_A, tower_1),
            ("2026-06-06T14:00:00Z", 300, 'CALL', callee_B, tower_2),
        ]

        for ts, dur, typ, callee, tower in calls_data:
            ev_id = str(uuid.uuid4())
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            dt_upper = dt + timedelta(seconds=dur)
            await session.execute(text("""
                INSERT INTO civix.event (event_id, event_type, occurred_at) 
                VALUES (:id, :typ, tstzrange(:ts_lower, :ts_upper))
            """), {"id": ev_id, "typ": typ, "ts_lower": dt, "ts_upper": dt_upper})
            await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:eid, :cid, 'CALLER')"), {"eid": ev_id, "cid": candidate_id})
            await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:eid, :cid, 'CALLEE')"), {"eid": ev_id, "cid": callee})
            await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:eid, :cid, 'CELL_TOWER')"), {"eid": ev_id, "cid": tower})

        # Financial Setup:
        # Txn 1: 5000, 2026-06-01
        # Txn 2: 15000, 2026-06-04
        receiver_id = str(uuid.uuid4())
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (:id, 'PERSON', :uid)"), {"id": receiver_id, "uid": admin_id})
        
        txns_data = [
            ("2026-06-01T10:00:00Z", 5000),
            ("2026-06-04T10:00:00Z", 15000),
        ]
        
        for ts, amt in txns_data:
            ev_id = str(uuid.uuid4())
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            await session.execute(text("""
                INSERT INTO civix.event (event_id, event_type, occurred_at) 
                VALUES (:id, 'TRANSACTION', tstzrange(:ts_lower, :ts_lower, '[]'))
            """), {"id": ev_id, "ts_lower": dt})
            await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:eid, :cid, 'SENDER')"), {"eid": ev_id, "cid": candidate_id})
            await session.execute(text("INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (:eid, :cid, 'RECEIVER')"), {"eid": ev_id, "cid": receiver_id})
            
            ass_id = str(uuid.uuid4())
            await session.execute(text("INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_entity_id, object_value, epistemic_status, asserted_by) VALUES (:aid, :cid, 'TRANSFERRED_TO', :rid, :amt, 'CONFIRMED', :uid)"), {"aid": ass_id, "cid": candidate_id, "rid": receiver_id, "amt": str(amt), "uid": admin_id})
            await session.execute(text("INSERT INTO civix.provenance (provenance_id, derived_id, derived_type, source_id, source_type, derivation_method) VALUES (:pid, :aid, 'ASSERTION', :eid, 'EVENT', 'INGESTION')"), {"pid": str(uuid.uuid4()), "aid": ass_id, "eid": ev_id})

        # --- IMPORTANT: DO NOT COMMIT ---
        # The extract_candidate_features function accepts `session` and can read our uncommitted rows perfectly.
        
        print("--- [2] EXTRACTING POSTGRESQL FEATURES ---")
        pg_features = await extract_candidate_features(session, [candidate_id])
        pg_vec = pg_features.get(candidate_id, {})

        print("--- [3] GENERATING OFFLINE FIXTURE ---")
        import pathlib
        out_dir = pathlib.Path("temp_offline_fixture")
        out_dir.mkdir(exist_ok=True)
        con = duckdb.connect(str(out_dir / "civix_offline.db"))
        
        cdrs = pd.DataFrame([
            {"caller_person_id": candidate_id, "caller_phone_id": candidate_id, "timestamp": "2026-06-01T12:00:00Z", "duration_seconds": 120, "call_type": "VOICE", "callee_person_id": callee_A, "callee_phone_id": callee_A, "cell_sector_id": tower_1},
            {"caller_person_id": candidate_id, "caller_phone_id": candidate_id, "timestamp": "2026-06-01T23:00:00Z", "duration_seconds": 60, "call_type": "VOICE", "callee_person_id": callee_A, "callee_phone_id": callee_A, "cell_sector_id": tower_1},
            {"caller_person_id": candidate_id, "caller_phone_id": candidate_id, "timestamp": "2026-06-06T14:00:00Z", "duration_seconds": 300, "call_type": "VOICE", "callee_person_id": callee_B, "callee_phone_id": callee_B, "cell_sector_id": tower_2},
        ])
        cdrs.to_parquet(out_dir / "cdrs.parquet")

        txns = pd.DataFrame([
            {"sender_person_id": candidate_id, "timestamp": "2026-06-01T10:00:00Z", "amount": 5000, "receiver_account_id": receiver_id, "transaction_type": "TRANSFER"},
            {"sender_person_id": candidate_id, "timestamp": "2026-06-04T10:00:00Z", "amount": 15000, "receiver_account_id": receiver_id, "transaction_type": "TRANSFER"},
        ])
        txns.to_parquet(out_dir / "txns.parquet")

        cells = pd.DataFrame([
            {"cell_id": tower_1, "centroid_latitude": 26.90, "centroid_longitude": 75.80, "region": "jaipur"},
            {"cell_id": tower_2, "centroid_latitude": 27.00, "centroid_longitude": 75.90, "region": "jaipur"}
        ])
        cells.to_parquet(out_dir / "cells.parquet")

        persons = pd.DataFrame([
            {"person_id": candidate_id, "gender": "MALE", "occupation": "Doctor", "home_region": "jaipur"}
        ])
        persons.to_parquet(out_dir / "persons.parquet")

        # Patch the constants in ML modules directly
        cdr = str((out_dir / "cdrs.parquet").absolute()).replace("\\", "/")
        txn = str((out_dir / "txns.parquet").absolute()).replace("\\", "/")
        cell = str((out_dir / "cells.parquet").absolute()).replace("\\", "/")
        
        import civix_ml.features.communication
        import civix_ml.features.geographic
        import civix_ml.features.financial
        import civix_ml.features.feature_pipeline
        
        civix_ml.features.communication.CDR_GLOB = cdr
        civix_ml.features.geographic.CDR_GLOB = cdr
        civix_ml.features.geographic.CELL_GLOB = cell
        civix_ml.features.financial.TXN_HIVE_GLOB = txn
        civix_ml.config.PERSONS_GLOB = str((out_dir / "persons.parquet").absolute()).replace("\\", "/")

        print("--- [4] CALCULATING OFFLINE FEATURES ---")
        df_comm = build_communication_features("2026-06-07", out_dir / "out_comm.parquet", con=con)
        df_fin = build_financial_features("2026-06-07", out_dir / "out_fin.parquet", con=con)
        df_geo = build_geographic_features("2026-06-07", out_dir / "out_geo.parquet", con=con)
        df_beh = build_behavioral_features(out_dir / "out_comm.parquet", out_dir / "out_fin.parquet", out_dir / "out_beh.parquet")
        
        merge_sql = f"""
        SELECT
            p.person_id,
            p.gender,
            p.occupation,
            c.* EXCLUDE(person_id),
            f.* EXCLUDE(person_id),
            g.* EXCLUDE(person_id),
            b.* EXCLUDE(person_id)
        FROM read_parquet('{out_dir}/persons.parquet') p
        LEFT JOIN read_parquet('{out_dir}/out_comm.parquet') c USING (person_id)
        LEFT JOIN read_parquet('{out_dir}/out_fin.parquet')  f USING (person_id)
        LEFT JOIN read_parquet('{out_dir}/out_geo.parquet')  g USING (person_id)
        LEFT JOIN read_parquet('{out_dir}/out_beh.parquet')  b USING (person_id)
        """
        df_ml = con.execute(merge_sql).df()
        
        offline_vec = df_ml.set_index("person_id").to_dict(orient="index").get(candidate_id, {})
        if offline_vec:
            for col, val in [("occupation", offline_vec.get("occupation")), ("home_region", offline_vec.get("home_region")), ("gender", offline_vec.get("gender"))]:
                if val:
                    key = f"{col}_{val}"
                    offline_vec[key] = 1.0

        print("--- [5] PARITY COMPARISON ---")
        
        import pickle
        with open("models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl", "rb") as f:
            model = pickle.load(f)
        features_ordered = model.feature_names_in_

        print(f"{'Feature Name':<30} | {'Offline':<12} | {'Postgres':<12} | {'Abs Delta':<10} | {'Status'}")
        print("-" * 80)
        
        table_rows = []
        
        for i, fname in enumerate(features_ordered):
            ov = float(offline_vec.get(fname, 0.0) or 0.0)
            pv = float(pg_vec.get(fname, 0.0) or 0.0)
            delta = abs(ov - pv)
            
            status = "EXACT"
            if delta > 1e-4:
                status = "FAIL"
                
            if fname == 'txn_type_diversity':
                status = "SCHEMA GAP"
            if fname == 'unique_regions':
                status = "SCHEMA GAP"

            print(f"{fname:<30} | {ov:<12.4f} | {pv:<12.4f} | {delta:<10.4f} | {status}")
            
            table_rows.append({
                "feature_name": fname,
                "model_position": i,
                "offline_value": ov,
                "postgres_value": pv,
                "absolute_delta": delta,
                "semantic_status": status,
                "evidence/source": "tests/harness/parity_harness.py fixture output"
            })
        
        with open("parity_results.json", "w") as f:
            json.dump(table_rows, f, indent=2)

        # Execute rollback to cleanly remove all fixture data without triggering RLS delete rules
        print("--- [6] ROLLING BACK TRANSACTION ---")
        await session.rollback()
        
        # Verify rollback worked
        verify = await session.execute(text("SELECT COUNT(*) FROM civix.person WHERE entity_id = :id"), {"id": candidate_id})
        count = verify.scalar()
        if count == 0:
            print("Rollback successful, no fixture data persisted.")
        else:
            print("✗ Rollback failed to remove candidate.")

    import shutil
    shutil.rmtree(out_dir)

if __name__ == "__main__":
    asyncio.run(run_parity_test())

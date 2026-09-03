import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
import json
import asyncio

from civix_api.main import app
from civix_api.config import settings

def create_token(sub: str, role: str = "INVESTIGATOR") -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600),
        "role": role # Usually backend doesn't check JWT role for cases if case_access is used, but just in case
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.fixture
async def setup_lead(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    # 1. Create a Case
    case_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, created_by)
        VALUES (:cid, :cnum, 'Lead Disp Test Case', 'CRIMINAL', 'TestJur', 'OPEN', :uid)
    """), {"cid": case_id, "cnum": f"TC-{uuid4().hex[:6]}", "uid": user_id})

    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:aid, :cid, :uid, 'WRITE', :uid)
    """), {"aid": uuid4(), "cid": case_id, "uid": user_id})

    # Create entities and dependencies for Lead
    gen_run_id = uuid4()
    candidate_id = uuid4()
    
    await db_session.execute(text("""
        INSERT INTO civix.dataset (dataset_id, name, dataset_type) 
        VALUES (:ds, 'TEST_DATASET_' || substr(cast(gen_random_uuid() as text), 1, 8), 'SYNTHETIC_TEST')
    """), {"ds": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.scenario (scenario_id, name, config_metadata) 
        VALUES (:sc, 'TEST_SCENARIO', '{}')
    """), {"sc": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.generation_run (generation_run_id, dataset_id, scenario_id, generator_version, run_timestamp, world_seed) 
        VALUES (:gen_id, :ds_id, :sc_id, 'TEST_V1', now(), 42)
    """), {"gen_id": gen_run_id, "ds_id": gen_run_id, "sc_id": gen_run_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, created_by, generation_run_id)
        VALUES (:c1, 'PERSON', :uid, :gen_id)
    """), {"c1": candidate_id, "uid": user_id, "gen_id": gen_run_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:c1, 'Test Candidate', 'MALE', :gen_id)
    """), {"c1": candidate_id, "gen_id": gen_run_id})

    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(user_id)})
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :c1, 'SUSPECT', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_id, "c1": candidate_id, "uid": user_id, "gen_id": gen_run_id})
    
    analysis_run_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.analysis_run (run_id, model_name, model_version, algorithm_type, started_at, initiated_by)
        VALUES (:run_id, 'test_model', '1.0', 'XGBOOST', now(), :uid)
    """), {"run_id": analysis_run_id, "uid": user_id})

    lead_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.investigative_lead (
            lead_id, case_id, target_entity_id, hypothesis_id,
            generated_by_run_id, generated_by_person, ai_confidence,
            lead_text, priority, status
        ) VALUES (
            :lid, :cid, :tid, NULL, :run_id, :uid, 0.9,
            'Test lead for disp', 'HIGH', 'OPEN'
        )
    """), {
        "lid": lead_id, "cid": case_id, "tid": candidate_id, 
        "run_id": analysis_run_id, "uid": user_id
    })
    
    # Also create a READ_ONLY user
    ro_user_id = await create_test_user()
    ro_token = create_token(sub=str(ro_user_id))
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:aid, :cid, :uid, 'READ', :uid)
    """), {"aid": uuid4(), "cid": case_id, "uid": ro_user_id})

    # Create a completely separate case and lead for cross-case tests
    case_b_id = uuid4()
    lead_b_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, created_by)
        VALUES (:cid, :cnum, 'Case B', 'CRIMINAL', 'TestJur', 'OPEN', :uid)
    """), {"cid": case_b_id, "cnum": f"CB-{uuid4().hex[:6]}", "uid": user_id})
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:aid, :cid, :uid, 'WRITE', :uid)
    """), {"aid": uuid4(), "cid": case_b_id, "uid": user_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :c1, 'SUSPECT', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_b_id, "c1": candidate_id, "uid": user_id, "gen_id": gen_run_id})

    await db_session.execute(text("""
        INSERT INTO civix.investigative_lead (
            lead_id, case_id, target_entity_id, hypothesis_id,
            generated_by_run_id, generated_by_person, ai_confidence,
            lead_text, priority, status
        ) VALUES (
            :lid, :cid, :tid, NULL, :run_id, :uid, 0.9,
            'Test lead B', 'HIGH', 'OPEN'
        )
    """), {
        "lid": lead_b_id, "cid": case_b_id, "tid": candidate_id, 
        "run_id": analysis_run_id, "uid": user_id
    })
    
    await db_session.commit()

    return {
        "case_id": case_id, "lead_id": lead_id, "token": token, "user_id": user_id,
        "ro_token": ro_token, "ro_user_id": ro_user_id,
        "case_b_id": case_b_id, "lead_b_id": lead_b_id
    }

@pytest.mark.asyncio
async def test_disposition_unauthenticated(setup_lead):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", json={"status": "CLOSED", "disposition_notes": "X"})
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_disposition_rbac(setup_lead, db_session):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    ro_token = setup_lead["ro_token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "IN_PROGRESS", "disposition_notes": "X"},
                            headers={"Authorization": f"Bearer {ro_token}"})
        assert res.status_code == 404 # Due to permission_level check hiding the lead/case
        
        # Valid user
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "IN_PROGRESS", "disposition_notes": "started"},
                            headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert res.json()["status"] == "IN_PROGRESS"

@pytest.mark.asyncio
async def test_disposition_case_isolation(setup_lead):
    case_id = setup_lead["case_id"]
    lead_b_id = setup_lead["lead_b_id"] # belongs to case B
    token = setup_lead["token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_b_id}/disposition", 
                            json={"status": "CLOSED", "disposition_notes": "X"},
                            headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 404

@pytest.mark.asyncio
async def test_disposition_valid_transitions(setup_lead):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # OPEN -> IN_PROGRESS
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "IN_PROGRESS", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        
        # IN_PROGRESS -> DEFERRED
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "DEFERRED", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        
        # DEFERRED -> IN_PROGRESS
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "IN_PROGRESS", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

        # IN_PROGRESS -> CONFIRMED (Terminal)
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "CONFIRMED", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_disposition_invalid_transitions(setup_lead):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # OPEN -> CONFIRMED (invalid)
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "CONFIRMED", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 409
        
        # OPEN -> CLOSED (valid, terminal)
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "CLOSED", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        
        # CLOSED -> OPEN (invalid, terminal)
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "OPEN", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 409

@pytest.mark.asyncio
async def test_disposition_idempotency_and_audit(setup_lead, db_session):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Initial: OPEN -> IN_PROGRESS
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "IN_PROGRESS", "disposition_notes": "step 1"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        
        # Check audit table for the first transition
        res_audit = await db_session.execute(text("SELECT * FROM civix.audit_event WHERE target_id = :lid AND action = 'LEAD_DISPOSITION'"), {"lid": lead_id})
        audits = res_audit.fetchall()
        assert len(audits) == 1
        meta = audits[0].metadata
        assert meta["previous_status"] == "OPEN"
        assert meta["new_status"] == "IN_PROGRESS"
        
        # Idempotent repeat: IN_PROGRESS -> IN_PROGRESS
        res2 = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                             json={"status": "IN_PROGRESS", "disposition_notes": "step 2"}, headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 200
        
        # Verify no duplicate audit event was generated
        res_audit = await db_session.execute(text("SELECT * FROM civix.audit_event WHERE target_id = :lid AND action = 'LEAD_DISPOSITION'"), {"lid": lead_id})
        audits = res_audit.fetchall()
        assert len(audits) == 1 # Still 1

@pytest.mark.asyncio
async def test_disposition_concurrency(setup_lead):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    
    async def make_request(status_str):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            return await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                                 json={"status": status_str, "disposition_notes": "concurrent"}, 
                                 headers={"Authorization": f"Bearer {token}"})
            
    # Send simultaneous requests for terminal states
    results = await asyncio.gather(
        make_request("CLOSED"),
        make_request("FALSE_POSITIVE")
    )
    
    status_codes = [r.status_code for r in results]
    assert 200 in status_codes
    assert 409 in status_codes # One wins, the other sees a terminal state and fails

@pytest.mark.asyncio
async def test_disposition_cdc_outbox(setup_lead, db_session):
    case_id = setup_lead["case_id"]
    lead_id = setup_lead["lead_id"]
    token = setup_lead["token"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post(f"/api/v1/cases/{case_id}/leads/{lead_id}/disposition", 
                            json={"status": "FALSE_POSITIVE", "disposition_notes": "A"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        
    # Check outbox
    res_outbox = await db_session.execute(text("SELECT * FROM civix.outbox WHERE entity_id = :lid ORDER BY created_at DESC"), {"lid": lead_id})
    outbox_rows = res_outbox.fetchall()
    assert len(outbox_rows) >= 1
    # We expect an UPDATE event on investigative_lead
    # outbox_rows[0].entity_type == 'investigative_lead'
    assert outbox_rows[0].entity_type == 'investigative_lead'
    assert outbox_rows[0].action == 'UPDATE'

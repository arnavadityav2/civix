import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
import copy
import asyncio

from civix_api.main import app
from civix_api.config import settings
from civix_api.dependencies import get_db_session
import asyncpg
from unittest.mock import patch, MagicMock

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_get_leads_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/cases/{uuid4()}/leads")
    assert response.status_code == 401
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(f"/api/v1/cases/{uuid4()}/leads/generate", json={"hypothesis_id": None})
    assert response.status_code == 401
    
    # Invalid JWT
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/cases/{uuid4()}/leads", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_leads_case_authorization_rls(db_session, create_test_user):
    user_a = await create_test_user()
    user_b = await create_test_user()
    
    token_a = create_token(sub=str(user_a))
    token_b = create_token(sub=str(user_b))
    
    # User A creates a case
    case_a_num = f"CA-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_a = await ac.post("/api/v1/cases", json={
            "case_number": case_a_num, "title": "Case A", "case_type": "CRIMINAL", "jurisdiction": "Jur A"
        }, headers={"Authorization": f"Bearer {token_a}"})
        case_a_id = res_a.json()["case_id"]

    # Insert a candidate entity and a lead manually to test GET isolation
    gen_run_id = uuid4()
    candidate_id = uuid4()
    lead_id = uuid4()
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
    """), {"c1": candidate_id, "uid": user_a, "gen_id": gen_run_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:c1, 'Test Candidate', 'MALE', :gen_id)
    """), {"c1": candidate_id, "gen_id": gen_run_id})

    # Temporarily set RLS to insert into case_entity_role
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a)})
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :c1, 'SUSPECT', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_a_id, "c1": candidate_id, "uid": user_a, "gen_id": gen_run_id})
    
    # We need an analysis_run for the lead
    analysis_run_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.analysis_run (run_id, model_name, model_version, algorithm_type, started_at, initiated_by)
        VALUES (:run_id, 'test_model', '1.0', 'XGBOOST', now(), :uid)
    """), {"run_id": analysis_run_id, "uid": user_a})

    await db_session.execute(text("""
        INSERT INTO civix.investigative_lead (
            lead_id, case_id, target_entity_id, hypothesis_id,
            generated_by_run_id, generated_by_person, ai_confidence,
            lead_text, priority, status
        ) VALUES (
            :lid, :cid, :tid, NULL, :run_id, :uid, 0.9,
            'Test lead', 'HIGH', 'OPEN'
        )
    """), {
        "lid": lead_id, "cid": case_a_id, "tid": candidate_id, 
        "run_id": analysis_run_id, "uid": user_a
    })
    await db_session.commit()

    # User A requests leads (Authorized)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        leads_a = await ac.get(f"/api/v1/cases/{case_a_id}/leads", headers={"Authorization": f"Bearer {token_a}"})
        assert leads_a.status_code == 200
        leads_data = leads_a.json()
        assert len(leads_data) == 1
        assert leads_data[0]["lead_id"] == str(lead_id)
        assert leads_data[0]["target_entity_id"] == str(candidate_id)
        
    # User B requests leads for User A's case (Unauthorized)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        leads_b = await ac.get(f"/api/v1/cases/{case_a_id}/leads", headers={"Authorization": f"Bearer {token_b}"})
        assert leads_b.status_code == 404
        
    # Cleanup to prevent teardown FK violations
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a)})
    await db_session.execute(text("DELETE FROM civix.case_entity_role WHERE case_id = :cid"), {"cid": case_a_id})
    await db_session.commit() # RLS hides it
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        gen_b = await ac.post(f"/api/v1/cases/{case_a_id}/leads/generate", json={"hypothesis_id": None}, headers={"Authorization": f"Bearer {token_b}"})
        assert gen_b.status_code == 404

@pytest.mark.asyncio
@patch("civix_api.routers.leads.extract_candidate_features")
async def test_get_leads_integration(mock_extract, db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    # 1. Create a Case
    case_num = f"ML-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "ML Test", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        case_id = res.json()["case_id"]

        # Create another case for cross-case testing
        res_b = await ac.post("/api/v1/cases", json={
            "case_number": f"CB-{uuid4().hex[:6]}", "title": "Case B", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        case_b_id = res_b.json()["case_id"]

        # Create a hypothesis in Case B
        res_hyp_b = await ac.post(f"/api/v1/cases/{case_b_id}/hypotheses", json={
            "hypothesis_text": "Hypothesis B"
        }, headers={"Authorization": f"Bearer {token}"})
        hyp_b_id = res_hyp_b.json()["hypothesis_id"]

    candidate_1_id = uuid4()
    candidate_2_id = uuid4()
    
    ds_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.dataset (dataset_id, name, dataset_type) 
        VALUES (:ds, 'TEST_DATASET_' || substr(cast(gen_random_uuid() as text), 1, 8), 'SYNTHETIC_TEST')
    """), {"ds": ds_id})

    sc_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.scenario (scenario_id, name, config_metadata) 
        VALUES (:sc, 'TEST_SCENARIO', '{}')
    """), {"sc": sc_id})

    gen_run_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.generation_run (generation_run_id, dataset_id, scenario_id, generator_version, run_timestamp, world_seed) 
        VALUES (:gen_id, :ds_id, :sc_id, 'TEST_V1', now(), 42)
    """), {"gen_id": gen_run_id, "ds_id": ds_id, "sc_id": sc_id})

    # Insert candidates directly using the authenticated db_session
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, created_by, generation_run_id)
        VALUES (:c1, 'PERSON', :uid, :gen_id), (:c2, 'PERSON', :uid, :gen_id)
    """), {"c1": candidate_1_id, "c2": candidate_2_id, "uid": user_id, "gen_id": gen_run_id})

    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:c1, 'Alice Candidate', 'FEMALE', :gen_id), (:c2, 'Bob Candidate', 'MALE', :gen_id)
    """), {"c1": candidate_1_id, "c2": candidate_2_id, "gen_id": gen_run_id})

    # Set RLS context so the insert passes the WITH CHECK constraint
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
    
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :c1, 'SUSPECT', :uid, :gen_id), (:r2, :cid, :c2, 'SUSPECT', :uid, :gen_id)
    """), {"r1": uuid4(), "r2": uuid4(), "cid": case_id, "c1": candidate_1_id, "c2": candidate_2_id, "uid": user_id, "gen_id": gen_run_id})
    await db_session.commit()

    # Mock extract_candidate_features to return a dictionary
    features_dict = {
        'total_calls': 0.0, 'active_days': 0.0, 'unique_contacts': 0.0, 'unique_cell_sectors': 0.0, 'voice_calls': 0.0, 'sms_count': 0.0,
        'data_sessions': 0.0, 'median_duration_sec': 0.0, 'short_call_ratio': 0.0, 'night_call_count': 0.0, 'night_call_ratio': 0.0,
        'weekend_call_ratio': 0.0, 'calls_per_active_day': 0.0, 'contact_concentration': 0.0, 'unique_counterparties': 0.0,
        'txn_type_diversity': 0.0, 'total_sent_amount': 0.0, 'avg_txn_amount': 0.0, 'median_txn_amount': 0.0, 'max_txn_amount': 0.0,
        'min_txn_amount': 0.0, 'std_txn_amount': 0.0, 'high_value_txn_count': 0.0, 'high_value_txn_ratio': 0.0, 'amount_concentration': 0.0,
        'unique_sectors': 0.0, 'unique_regions': 0.0, 'geo_spread_degrees': 0.0, 'lat_stddev': 0.0, 'lon_stddev': 0.0,
        'location_active_days': 0.0, 'cross_region_ratio': 0.0, 'active_day_delta': 0.0, 'calls_per_txn': 0.0, 'call_duration_cv': 0.0,
        'txn_amount_cv': 0.0, 'comm_span_days': 0.0, 'txn_span_days': 0.0, 'dual_concentration': 0.0, 'total_network_size': 0.0,
        'gender_MALE': 0.0, 'gender_OTHER': 0.0, 'occupation_Businessman': 0.0, 'occupation_Carpenter': 0.0, 'occupation_Contractor': 0.0,
        'occupation_Doctor': 0.0, 'occupation_Driver': 0.0, 'occupation_Electrician': 0.0, 'occupation_Engineer': 0.0, 'occupation_Farmer': 0.0,
        'occupation_Government Employee': 0.0, 'occupation_Hawker': 0.0, 'occupation_Housewife': 0.0, 'occupation_Laborer': 0.0,
        'occupation_Mechanic': 0.0, 'occupation_Police Officer': 0.0, 'occupation_Shopkeeper': 0.0, 'occupation_Student': 0.0,
        'occupation_Tailor': 0.0, 'occupation_Teacher': 0.0, 'occupation_Trader': 0.0, 'home_region_alwar': 0.0, 'home_region_bharatpur': 0.0,
        'home_region_bikaner': 0.0, 'home_region_jaipur': 0.0, 'home_region_jodhpur': 0.0, 'home_region_kota': 0.0, 'home_region_pali': 0.0,
        'home_region_sikar': 0.0, 'home_region_udaipur': 0.0
    }
    
    mock_extract.return_value = {
        str(candidate_1_id): features_dict.copy(),
        str(candidate_2_id): features_dict.copy()
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        runs_count_before = await db_session.execute(text("SELECT count(*) FROM civix.analysis_run"))
        runs_before = runs_count_before.scalar()
        
        # Cross-case hypothesis test
        res_cross = await ac.post(f"/api/v1/cases/{case_id}/leads/generate", json={"hypothesis_id": hyp_b_id}, headers={"Authorization": f"Bearer {token}"})
        print("res_cross json:", res_cross.json())
        assert res_cross.status_code == 400
        assert "Foreign key or integrity violation" in res_cross.json()["detail"]
    
        # Ensure rollback was complete (no runs or leads)
        runs_count_after = await db_session.execute(text("SELECT count(*) FROM civix.analysis_run"))
        assert runs_count_after.scalar() == runs_before

        # Nullable hypothesis generation
        leads_res = await ac.post(f"/api/v1/cases/{case_id}/leads/generate", json={"hypothesis_id": None}, headers={"Authorization": f"Bearer {token}"})
        
        assert leads_res.status_code == 200
        data = leads_res.json()
        
        assert data["case_id"] == case_id
        assert "behavioral_xgboost" in data["model_version"]
        assert len(data["leads"]) == 2
        
        leads = data["leads"]
        assert "priority" in leads[0]
        assert "status" in leads[0]

        assert "lead_id" in leads[0]
        assert "target_entity_id" in leads[0]
        assert "ai_confidence" in leads[0]
        assert "generated_by_run_id" in leads[0]
        assert leads[0]["status"] == "OPEN"
        assert leads[0]["hypothesis_id"] is None
        
        run_id = leads[0]["generated_by_run_id"]
        assert run_id is not None
        
        # Verify GET retrieves the DB records without side-effects
        mock_extract.reset_mock()
        get_res = await ac.get(f"/api/v1/cases/{case_id}/leads", headers={"Authorization": f"Bearer {token}"})
        assert get_res.status_code == 200
        get_data = get_res.json()
        
        assert len(get_data) == 2
        assert get_data[0]["lead_id"] in [leads[0]["lead_id"], leads[1]["lead_id"]]
        mock_extract.assert_not_called() # Ensure GET did not call ML feature extraction
        
    # Cleanup case_entity_role
    await db_session.execute(text("DELETE FROM civix.case_entity_role WHERE case_id = :cid"), {"cid": case_id})
    await db_session.commit()

@pytest.fixture
async def setup_lead(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
    
    # 1. Create a Case
    case_id = uuid4()
    
    # Insert case_access FIRST because the RLS policy for investigative_case
    # requires the user to already have access (via the deferred FK).
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:a_id, :cid, :uid, 'WRITE', :uid)
    """), {"a_id": uuid4(), "cid": case_id, "uid": user_id})

    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, lead_investigator_id, opened_at)
        VALUES (:cid, :cnum, 'Lead Disp Test Case', 'CRIMINAL', 'TestJur', 'OPEN', :uid, now())
    """), {"cid": case_id, "cnum": f"TC-{uuid4().hex[:6]}", "uid": user_id})

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

    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
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
        VALUES (:aid, :cid, :uid, 'READ', :gid)
    """), {"aid": uuid4(), "cid": case_id, "uid": ro_user_id, "gid": user_id})

    # Create a completely separate case and lead for cross-case tests
    case_b_id = uuid4()
    lead_b_id = uuid4()
    
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
    
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:aid, :cid, :uid, 'WRITE', :uid)
    """), {"aid": uuid4(), "cid": case_b_id, "uid": user_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, lead_investigator_id, opened_at)
        VALUES (:cid, :cnum, 'Case B', 'CRIMINAL', 'TestJur', 'OPEN', :uid, now())
    """), {"cid": case_b_id, "cnum": f"CB-{uuid4().hex[:6]}", "uid": user_id})
    
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

    yield {
        "case_id": case_id, "lead_id": lead_id, "token": token, "user_id": user_id,
        "ro_token": ro_token, "ro_user_id": ro_user_id,
        "case_b_id": case_b_id, "lead_b_id": lead_b_id
    }
    
    # Teardown
    # await db_session.execute(text("DELETE FROM civix.audit_event WHERE case_context_id IN (:c1, :c2)"), {"c1": case_id, "c2": case_b_id})
    await db_session.execute(text("DELETE FROM civix.outbox WHERE entity_id IN (:l1, :l2)"), {"l1": lead_id, "l2": lead_b_id})
    await db_session.execute(text("DELETE FROM civix.investigative_lead WHERE case_id IN (:c1, :c2)"), {"c1": case_id, "c2": case_b_id})
    await db_session.execute(text("DELETE FROM civix.case_entity_role WHERE case_id IN (:c1, :c2)"), {"c1": case_id, "c2": case_b_id})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id IN (:c1, :c2)"), {"c1": case_id, "c2": case_b_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id IN (:c1, :c2)"), {"c1": case_id, "c2": case_b_id})
    await db_session.commit()

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
    assert outbox_rows[0].entity_type == 'investigative_lead'
    assert outbox_rows[0].action == 'UPSERT_NODE'
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

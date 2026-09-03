import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from civix_api.main import app
from civix_api.config import settings

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.fixture
async def setup_search_entities(db_session, create_test_user):
    user_admin = await create_test_user()
    user_no_access = await create_test_user()
    user_other_admin = await create_test_user()
    
    token_admin = create_token(sub=str(user_admin))
    token_no_access = create_token(sub=str(user_no_access))
    
    case_id = uuid4()
    case_id2 = uuid4()
    
    # Temporarily set RLS to insert as user_admin
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})
    
    # Case 1 (user_admin has ADMIN access)
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:a1, :cid, :uid, 'ADMIN', :uid)
    """), {"a1": uuid4(), "cid": case_id, "uid": user_admin})
    
    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, lead_investigator_id, opened_at)
        VALUES (:cid, :cnum, 'Search Test Case', 'CRIMINAL', 'TestJur', 'OPEN', :uid, now())
    """), {"cid": case_id, "cnum": f"TC-{uuid4().hex[:6]}", "uid": user_admin})
    
    # Temporarily set RLS to insert Case 2 as user_other_admin
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_other_admin)})

    # Case 2 (user_other_admin has ADMIN)
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (:a1, :cid, :uid, 'ADMIN', :uid)
    """), {"a1": uuid4(), "cid": case_id2, "uid": user_other_admin})

    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, lead_investigator_id, opened_at)
        VALUES (:cid, :cnum, 'Inaccessible Case', 'CRIMINAL', 'TestJur', 'OPEN', :uid, now())
    """), {"cid": case_id2, "cnum": f"TC-{uuid4().hex[:6]}", "uid": user_other_admin})

    # Revert to user_admin for the rest of setup
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})
    
    # Gen run
    gen_run_id = uuid4()
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

    entities = []

    def add_entity(entity_id, e_type, status):
        entities.append(entity_id)
        return text("""
            INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_by, generation_run_id)
            VALUES (:eid, CAST(:etype AS civix.entity_type_enum), CAST(:status AS civix.visibility_status_enum), :uid, :gen_id)
        """).bindparams(eid=entity_id, etype=e_type, status=status, uid=user_admin, gen_id=gen_run_id)

    # 1. Accessible Person
    p1_id = uuid4()
    await db_session.execute(add_entity(p1_id, 'PERSON', 'ACTIVE'))
    await db_session.execute(text("INSERT INTO civix.person (entity_id, display_name, generation_run_id) VALUES (:eid, 'John Doe Search', :gen)"), {"eid": p1_id, "gen": gen_run_id})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id, "eid": p1_id, "uid": user_admin, "gen": gen_run_id})

    # 2. Accessible Device
    d1_id = uuid4()
    d1_imei = uuid4().hex[:15]
    await db_session.execute(add_entity(d1_id, 'DEVICE', 'ACTIVE'))
    await db_session.execute(text("INSERT INTO civix.device (entity_id, imei, device_type, generation_run_id) VALUES (:eid, :imei, 'SMARTPHONE', :gen)"), {"eid": d1_id, "imei": d1_imei, "gen": gen_run_id})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUBJECT_DEVICE', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id, "eid": d1_id, "uid": user_admin, "gen": gen_run_id})

    # 3. Inaccessible Person (belongs to Case 2 only)
    p2_id = uuid4()
    await db_session.execute(add_entity(p2_id, 'PERSON', 'ACTIVE'))
    await db_session.execute(text("INSERT INTO civix.person (entity_id, display_name, generation_run_id) VALUES (:eid, 'Hidden John Doe', :gen)"), {"eid": p2_id, "gen": gen_run_id})
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_other_admin)})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id2, "eid": p2_id, "uid": user_other_admin, "gen": gen_run_id})
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})

    # 4. Tombstoned Person (belongs to Case 1)
    p3_id = uuid4()
    await db_session.execute(add_entity(p3_id, 'PERSON', 'TOMBSTONED'))
    await db_session.execute(text("INSERT INTO civix.person (entity_id, display_name, generation_run_id) VALUES (:eid, 'Ghost John Doe', :gen)"), {"eid": p3_id, "gen": gen_run_id})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id, "eid": p3_id, "uid": user_admin, "gen": gen_run_id})

    # 5. Cross-Case Person (belongs to Case 1 and Case 2)
    p4_id = uuid4()
    await db_session.execute(add_entity(p4_id, 'PERSON', 'ACTIVE'))
    await db_session.execute(text("INSERT INTO civix.person (entity_id, display_name, generation_run_id) VALUES (:eid, 'Multi Case John', :gen)"), {"eid": p4_id, "gen": gen_run_id})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id, "eid": p4_id, "uid": user_admin, "gen": gen_run_id})
    
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_other_admin)})
    await db_session.execute(text("INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen)"), 
        {"r1": uuid4(), "cid": case_id2, "eid": p4_id, "uid": user_other_admin, "gen": gen_run_id})
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})

    await db_session.commit()

    yield {
        "p1_id": p1_id,
        "d1_id": d1_id,
        "d1_imei": d1_imei,
        "p2_id": p2_id,
        "p3_id": p3_id,
        "p4_id": p4_id,
        "tokens": {
            "admin": token_admin,
            "none": token_no_access
        }
    }
    



@pytest.mark.asyncio
async def test_search_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/search?q=John")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_search_validation(setup_search_entities):
    token = setup_search_entities["tokens"]["admin"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # q too short
        res = await ac.get("/api/v1/search?q=Jo", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 422
        
        # limit > 100
        res = await ac.get("/api/v1/search?q=John&limit=101", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 422
        
        # offset < 0
        res = await ac.get("/api/v1/search?q=John&offset=-1", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 422

@pytest.mark.asyncio
async def test_search_basic(setup_search_entities):
    token = setup_search_entities["tokens"]["admin"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Search for accessible person (ILIKE)
        res = await ac.get("/api/v1/search?q=John%20Doe%20Search", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["entity_id"] == str(setup_search_entities["p1_id"])
        assert data["results"][0]["entity_type"] == "PERSON"
        assert data["results"][0]["matched_field"] == "display_name"
        
        # Search for exact identifier
        imei = setup_search_entities["d1_imei"]
        res = await ac.get(f"/api/v1/search?q={imei}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert len(data["results"]) == 1
        assert data["results"][0]["entity_id"] == str(setup_search_entities["d1_id"])
        assert data["results"][0]["matched_field"] == "imei"

@pytest.mark.asyncio
async def test_search_entity_type_filter(setup_search_entities):
    token = setup_search_entities["tokens"]["admin"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # p1_id is John Doe Search, let's search just 'John' with wrong entity type
        res = await ac.get("/api/v1/search?q=John&entity_type=DEVICE", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert len(res.json()["results"]) == 0
        
        # Correct entity type
        res = await ac.get("/api/v1/search?q=John&entity_type=PERSON", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        results = res.json()["results"]
        # "John" will match p1 and p4
        assert len(results) == 2

@pytest.mark.asyncio
async def test_search_isolation_and_tombstone(setup_search_entities):
    token = setup_search_entities["tokens"]["admin"]
    token_none = setup_search_entities["tokens"]["none"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Tombstoned entity should NOT appear (Ghost John Doe)
        res = await ac.get("/api/v1/search?q=Ghost", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert len(res.json()["results"]) == 0
        
        # Inaccessible entity should NOT appear (Hidden John Doe)
        res = await ac.get("/api/v1/search?q=Hidden", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        assert len(res.json()["results"]) == 0
        
        # Another user with no access searching for 'John' shouldn't see anything
        res = await ac.get("/api/v1/search?q=John", headers={"Authorization": f"Bearer {token_none}"})
        assert res.status_code == 200
        assert len(res.json()["results"]) == 0

@pytest.mark.asyncio
async def test_search_duplicate_prevention(setup_search_entities):
    token = setup_search_entities["tokens"]["admin"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # p4 (Multi Case John) is in 2 cases, one of which admin has access to, the other not (or maybe he does? wait, I only gave admin access to case_id).
        # Actually I gave admin access to case_id, but NOT case_id2. Let's still search for 'Multi Case'.
        res = await ac.get("/api/v1/search?q=Multi%20Case", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        results = res.json()["results"]
        # Should only be returned once
        assert len(results) == 1
        assert results[0]["entity_id"] == str(setup_search_entities["p4_id"])

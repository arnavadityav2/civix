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
async def setup_entity(db_session, create_test_user):
    # Create 3 users for testing READ, WRITE, and ADMIN access
    user_admin = await create_test_user()
    user_write = await create_test_user()
    user_read = await create_test_user()
    user_no_access = await create_test_user()
    
    token_admin = create_token(sub=str(user_admin))
    token_write = create_token(sub=str(user_write))
    token_read = create_token(sub=str(user_read))
    token_no_access = create_token(sub=str(user_no_access))
    
    case_id = uuid4()
    
    # Temporarily set RLS to insert as user_admin
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})
    
    # Case accesses
    await db_session.execute(text("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES 
        (:a1, :cid, :u_admin, 'ADMIN', :u_admin),
        (:a2, :cid, :u_write, 'WRITE', :u_admin),
        (:a3, :cid, :u_read, 'READ', :u_admin)
    """), {
        "a1": uuid4(), "a2": uuid4(), "a3": uuid4(),
        "cid": case_id, "u_admin": user_admin, "u_write": user_write, "u_read": user_read
    })
    
    await db_session.execute(text("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, status, lead_investigator_id, opened_at)
        VALUES (:cid, :cnum, 'Entity Test Case', 'CRIMINAL', 'TestJur', 'OPEN', :uid, now())
    """), {"cid": case_id, "cnum": f"TC-{uuid4().hex[:6]}", "uid": user_admin})

    # Add Generation Run to avoid FK violations
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

    # 1. Accessible Person
    person_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_by, generation_run_id)
        VALUES (:eid, 'PERSON', 'ACTIVE', :uid, :gen_id)
    """), {"eid": person_id, "uid": user_admin, "gen_id": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:eid, 'Test Person', 'FEMALE', :gen_id)
    """), {"eid": person_id, "gen_id": gen_run_id})
    
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :eid, 'SUSPECT', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_id, "eid": person_id, "uid": user_admin, "gen_id": gen_run_id})

    # 2. Accessible Device (another subtype)
    device_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_by, generation_run_id)
        VALUES (:eid, 'DEVICE', 'ACTIVE', :uid, :gen_id)
    """), {"eid": device_id, "uid": user_admin, "gen_id": gen_run_id})
    device_imei = uuid4().hex[:15]
    await db_session.execute(text("""
        INSERT INTO civix.device (entity_id, imei, device_type, manufacturer, generation_run_id) 
        VALUES (:eid, :imei, 'SMARTPHONE', 'Apple', :gen_id)
    """), {"eid": device_id, "imei": device_imei, "gen_id": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :eid, 'SUBJECT_DEVICE', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_id, "eid": device_id, "uid": user_admin, "gen_id": gen_run_id})

    # 3. Tombstoned Entity (in same case)
    tombstoned_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_by, generation_run_id)
        VALUES (:eid, 'PERSON', 'TOMBSTONED', :uid, :gen_id)
    """), {"eid": tombstoned_id, "uid": user_admin, "gen_id": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:eid, 'Ghost Person', 'MALE', :gen_id)
    """), {"eid": tombstoned_id, "gen_id": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, assigned_by, generation_run_id) 
        VALUES (:r1, :cid, :eid, 'PERSON_OF_INTEREST', :uid, :gen_id)
    """), {"r1": uuid4(), "cid": case_id, "eid": tombstoned_id, "uid": user_admin, "gen_id": gen_run_id})

    # 4. Unassociated Entity
    unassoc_id = uuid4()
    await db_session.execute(text("""
        INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_by, generation_run_id)
        VALUES (:eid, 'PERSON', 'ACTIVE', :uid, :gen_id)
    """), {"eid": unassoc_id, "uid": user_admin, "gen_id": gen_run_id})
    await db_session.execute(text("""
        INSERT INTO civix.person (entity_id, display_name, gender, generation_run_id) 
        VALUES (:eid, 'Unassociated Person', 'MALE', :gen_id)
    """), {"eid": unassoc_id, "gen_id": gen_run_id})

    await db_session.commit()

    yield {
        "case_id": case_id,
        "person_id": person_id,
        "device_id": device_id,
        "tombstoned_id": tombstoned_id,
        "unassoc_id": unassoc_id,
        "tokens": {
            "admin": token_admin,
            "write": token_write,
            "read": token_read,
            "none": token_no_access
        }
    }
    
    # Teardown
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_admin)})
    await db_session.execute(text("DELETE FROM civix.case_entity_role WHERE case_id = :cid"), {"cid": case_id})
    await db_session.execute(text("DELETE FROM civix.person WHERE entity_id IN (:e1, :e2, :e3)"), 
                             {"e1": person_id, "e2": tombstoned_id, "e3": unassoc_id})
    await db_session.execute(text("DELETE FROM civix.device WHERE entity_id = :e1"), {"e1": device_id})
    await db_session.execute(text("DELETE FROM civix.entity WHERE entity_id IN (:e1, :e2, :e3, :e4)"),
                             {"e1": person_id, "e2": device_id, "e3": tombstoned_id, "e4": unassoc_id})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
    await db_session.commit()


@pytest.mark.asyncio
async def test_get_entity_unauthenticated():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/entities/{uuid4()}")
    assert response.status_code == 401
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get(f"/api/v1/entities/{uuid4()}", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_entity_malformed_uuid(setup_entity):
    token = setup_entity["tokens"]["admin"]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/entities/not-a-uuid", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_get_entity_access_levels(setup_entity):
    person_id = setup_entity["person_id"]
    tokens = setup_entity["tokens"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # READ access
        res = await ac.get(f"/api/v1/entities/{person_id}", headers={"Authorization": f"Bearer {tokens['read']}"})
        assert res.status_code == 200
        assert res.json()["entity"]["entity_id"] == str(person_id)

        # WRITE access
        res = await ac.get(f"/api/v1/entities/{person_id}", headers={"Authorization": f"Bearer {tokens['write']}"})
        assert res.status_code == 200
        
        # ADMIN access
        res = await ac.get(f"/api/v1/entities/{person_id}", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_get_entity_information_hiding(setup_entity):
    tokens = setup_entity["tokens"]
    person_id = setup_entity["person_id"]
    unassoc_id = setup_entity["unassoc_id"]
    tombstoned_id = setup_entity["tombstoned_id"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Nonexistent entity
        res = await ac.get(f"/api/v1/entities/{uuid4()}", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert res.status_code == 404
        
        # Cross-case/No-access entity
        res = await ac.get(f"/api/v1/entities/{person_id}", headers={"Authorization": f"Bearer {tokens['none']}"})
        assert res.status_code == 404
        
        # Unassociated entity (nobody can see it)
        res = await ac.get(f"/api/v1/entities/{unassoc_id}", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert res.status_code == 404
        
        # Tombstoned entity (even with case access)
        res = await ac.get(f"/api/v1/entities/{tombstoned_id}", headers={"Authorization": f"Bearer {tokens['admin']}"})
        assert res.status_code == 404

@pytest.mark.asyncio
async def test_get_entity_polymorphism(setup_entity):
    person_id = setup_entity["person_id"]
    device_id = setup_entity["device_id"]
    token = setup_entity["tokens"]["admin"]
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # PERSON subtype
        res = await ac.get(f"/api/v1/entities/{person_id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["entity"]["entity_type"] == "PERSON"
        assert "subtype_data" in data
        assert data["subtype_data"]["display_name"] == "Test Person"
        assert data["subtype_data"]["gender"] == "FEMALE"
        assert "imei" not in data["subtype_data"] # No cross-pollination
        assert "is_deceased" in data["subtype_data"]
        
        # DEVICE subtype
        res = await ac.get(f"/api/v1/entities/{device_id}", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert data["entity"]["entity_type"] == "DEVICE"
        assert data["subtype_data"]["device_type"] == "SMARTPHONE"
        assert data["subtype_data"]["imei"] is not None
        assert data["subtype_data"]["manufacturer"] == "Apple"
        assert "display_name" not in data["subtype_data"]

import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import text

@pytest.fixture(autouse=True)
def clear_token_override():
    yield
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    app.dependency_overrides.pop(get_current_user_from_token, None)

@pytest.fixture
def mock_investigator():
    return {
        "user_id": str(uuid4()),
        "username": f"inv1_{uuid4().hex[:8]}",
        "role": "INVESTIGATOR",
        "clearance_level": "SECRET"
    }

@pytest.fixture
def mock_readonly_user():
    return {
        "user_id": str(uuid4()),
        "username": f"read1_{uuid4().hex[:8]}",
        "role": "INVESTIGATOR", # Role doesn't matter as much as case_access
        "clearance_level": "SECRET"
    }

@pytest.fixture
def mock_admin():
    return {
        "user_id": str(uuid4()),
        "username": f"admin1_{uuid4().hex[:8]}",
        "role": "ADMIN",
        "clearance_level": "SECRET"
    }

@pytest.fixture
async def setup_case_and_entity(db_session, mock_investigator, mock_readonly_user, mock_admin):
    from civix_api.main import app
    from httpx import AsyncClient, ASGITransport
    import jwt
    from datetime import datetime, timedelta
    from civix_api.config import settings

    def create_token(sub: str) -> str:
        payload = {"sub": sub, "exp": datetime.utcnow() + timedelta(seconds=3600)}
        return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

    entity_id = uuid4()
    
    # Insert users
    for u in [mock_investigator, mock_readonly_user, mock_admin]:
        await db_session.execute(
            text(f"INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) VALUES ('{u['user_id']}', 'auth-{u['user_id']}', '{u['username']}', '{u['username']}', '{u['role']}', 'SECRET') ON CONFLICT DO NOTHING")
        )
    await db_session.commit()

    # Create case via API as admin
    token = create_token(sub=mock_admin['user_id'])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/cases", json={
            "case_number": f"CIV-TEST-{uuid4().hex[:6]}",
            "title": "Test Case",
            "case_type": "CRIMINAL",
            "jurisdiction": "Test Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        case_id = res.json()["case_id"]

    # Give write access to investigator and read to readonly user
    await db_session.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": mock_admin['user_id']})
    await db_session.execute(
        text(f"INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES ('{case_id}', '{mock_investigator['user_id']}', 'WRITE', '{mock_admin['user_id']}')")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES ('{case_id}', '{mock_readonly_user['user_id']}', 'READ', '{mock_admin['user_id']}')")
    )
    
    # Insert entity
    await db_session.execute(
        text(f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{entity_id}', 'PERSON')")
    )
    
    await db_session.commit()
    return {
        "case_id": str(case_id),
        "entity_id": str(entity_id)
    }

@pytest.mark.asyncio
async def test_link_entity_success(client: AsyncClient, setup_case_and_entity, mock_investigator, db_session):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUSPECT",
        "role_basis": "Identified in footage"
    }
    
    resp = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp.status_code == 201
    
    data = resp.json()
    assert data["entity_id"] == payload["entity_id"]
    assert data["role"] == payload["role"]
    assert data["role_basis"] == payload["role_basis"]
    assert "role_id" in data
    
    # Verify Audit Event
    audit_res = await db_session.execute(text(f"SELECT metadata FROM civix.audit_event WHERE action = 'WRITE' AND target_table = 'case_entity_role' AND target_id = '{data['role_id']}'"))
    audit_row = audit_res.first()
    assert audit_row is not None
    assert audit_row[0]["role"] == "SUSPECT"

@pytest.mark.asyncio
async def test_link_entity_duplicate_fails(client: AsyncClient, setup_case_and_entity, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUSPECT"
    }
    
    resp1 = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp1.status_code == 201
    
    # Second time should fail
    resp2 = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp2.status_code == 409
    assert "conflict" in resp2.json()["detail"].lower()

@pytest.mark.asyncio
async def test_link_entity_different_role_succeeds(client: AsyncClient, setup_case_and_entity, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload1 = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUSPECT"
    }
    resp1 = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload1)
    assert resp1.status_code == 201
    
    payload2 = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUBJECT_VEHICLE" # Same entity, different role (not logically sound for PERSON, but allowed by schema)
    }
    resp2 = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload2)
    assert resp2.status_code == 201

@pytest.mark.asyncio
async def test_link_entity_readonly_user_fails(client: AsyncClient, setup_case_and_entity, mock_readonly_user):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_readonly_user)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUSPECT"
    }
    
    resp = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_link_entity_admin_succeeds(client: AsyncClient, setup_case_and_entity, mock_admin):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_admin)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "WITNESS"
    }
    
    resp = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp.status_code == 201

@pytest.mark.asyncio
async def test_link_entity_not_found(client: AsyncClient, setup_case_and_entity, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "entity_id": str(uuid4()), # non-existent entity
        "role": "SUSPECT"
    }
    
    resp = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp.status_code == 400

@pytest.mark.asyncio
async def test_link_entity_case_not_found(client: AsyncClient, setup_case_and_entity, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "SUSPECT"
    }
    
    resp = await client.post(f"/api/v1/cases/{str(uuid4())}/entities", json=payload)
    assert resp.status_code == 403 # Since case_access won't exist either

@pytest.mark.asyncio
async def test_link_entity_invalid_enum(client: AsyncClient, setup_case_and_entity, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "entity_id": setup_case_and_entity["entity_id"],
        "role": "NOT_A_REAL_ROLE"
    }
    
    resp = await client.post(f"/api/v1/cases/{setup_case_and_entity['case_id']}/entities", json=payload)
    assert resp.status_code == 422

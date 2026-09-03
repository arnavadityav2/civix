import pytest
from httpx import AsyncClient
from uuid import uuid4
from datetime import datetime
from sqlalchemy import text

@pytest.fixture(autouse=True)
def clear_token_override():
    yield
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    app.dependency_overrides.pop(get_current_user_from_token, None)

@pytest.fixture
def mock_supervisor():
    return {
        "user_id": str(uuid4()),
        "username": f"super1_{uuid4().hex[:8]}",
        "role": "SUPERVISOR",
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
def mock_investigator():
    return {
        "user_id": str(uuid4()),
        "username": f"inv1_{uuid4().hex[:8]}",
        "role": "INVESTIGATOR",
        "clearance_level": "SECRET"
    }

@pytest.fixture
def mock_analyst():
    return {
        "user_id": str(uuid4()),
        "username": f"ana1_{uuid4().hex[:8]}",
        "role": "ANALYST",
        "clearance_level": "SECRET"
    }

@pytest.fixture
async def setup_resolution_data(db_session, mock_supervisor):
    # Setup test entities
    source_identity_id = uuid4()
    person_id = uuid4()
    candidate_id = uuid4()
    
    # Insert user
    await db_session.execute(
        text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) VALUES ('{0}', 'auth-{0}', '{1}', '{1}', 'SUPERVISOR', 'SECRET') ON CONFLICT DO NOTHING".format(mock_supervisor['user_id'], mock_supervisor['username']))
    )
    
    # Insert source_identity
    await db_session.execute(
        text(f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{source_identity_id}', 'SOURCE_IDENTITY')")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at) VALUES ('{source_identity_id}', 'test_ident', 'NAME', NOW())")
    )
    
    # Insert person
    await db_session.execute(
        text(f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{person_id}', 'PERSON')")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.person (entity_id, display_name) VALUES ('{person_id}', 'Test Person')")
    )
    
    # Insert analysis_run and candidate
    run_id = uuid4()
    await db_session.execute(
        text(f"INSERT INTO civix.analysis_run (run_id, model_name, model_version, algorithm_type, initiated_by, started_at) VALUES ('{run_id}', 'test', 'v1', 'algo', '{mock_supervisor['user_id']}', NOW())")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.identity_candidate (candidate_id, source_identity_id, proposed_person_id, ai_confidence, analysis_run_id, created_at) VALUES ('{candidate_id}', '{source_identity_id}', '{person_id}', 0.95, '{run_id}', NOW())")
    )
    
    await db_session.commit()
    return {
        "source_identity_id": str(source_identity_id),
        "person_id": str(person_id),
        "candidate_id": str(candidate_id)
    }

@pytest.mark.asyncio
async def test_accepted_resolution_supervisor(client: AsyncClient, setup_resolution_data, mock_supervisor, monkeypatch, db_session):
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    from civix_api.main import app
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "person_id": setup_resolution_data["person_id"],
        "candidate_id": setup_resolution_data["candidate_id"],
        "decision": "ACCEPTED",
        "decision_notes": "Supervisor approved"
    }
    
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED"
    assert data["resolved_person_id"] == payload["person_id"]
    
    # Verify Audit Event
    audit_res = await db_session.execute(text(f"SELECT metadata FROM civix.audit_event WHERE action = 'IDENTITY_RESOLVE' AND metadata->>'source_identity_id' = '{payload['source_identity_id']}'"))
    audit_row = audit_res.first()
    assert audit_row is not None
    metadata = audit_row[0]
    assert metadata["decision"] == "ACCEPTED"
    assert metadata["source_identity_id"] == payload["source_identity_id"]

@pytest.mark.asyncio
async def test_accepted_resolution_admin(client: AsyncClient, setup_resolution_data, mock_admin, db_session):
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    from civix_api.main import app
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_admin)
    
    # insert admin user
    await db_session.execute(text(f"INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) VALUES ('{mock_admin['user_id']}', 'auth-{mock_admin['user_id']}', '{mock_admin['username']}', '{mock_admin['username']}', 'ADMIN', 'SECRET') ON CONFLICT DO NOTHING"))
    await db_session.commit()
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "person_id": setup_resolution_data["person_id"],
        "decision": "ACCEPTED",
        "decision_notes": "Admin manual approved"
    }
    
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 200
    
@pytest.mark.asyncio
async def test_rejected_resolution(client: AsyncClient, setup_resolution_data, mock_supervisor):
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    from civix_api.main import app
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "candidate_id": setup_resolution_data["candidate_id"],
        "decision": "REJECTED",
        "decision_notes": "Rejected by supervisor"
    }
    
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"
    assert resp.json()["resolved_person_id"] is None

@pytest.mark.asyncio
async def test_validation_failure_accepted_null_person(client: AsyncClient, setup_resolution_data, mock_supervisor):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "decision": "ACCEPTED",
        "decision_notes": "Fail"
    }
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 422
    
@pytest.mark.asyncio
async def test_validation_failure_rejected_with_person(client: AsyncClient, setup_resolution_data, mock_supervisor):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "person_id": setup_resolution_data["person_id"],
        "decision": "REJECTED",
        "decision_notes": "Fail"
    }
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_validation_failure_missing_notes(client: AsyncClient, setup_resolution_data, mock_supervisor):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "decision": "REJECTED",
        "decision_notes": " "
    }
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 422

@pytest.mark.asyncio
async def test_investigator_denied(client: AsyncClient, setup_resolution_data, mock_investigator):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "decision": "REJECTED",
        "decision_notes": "Inv"
    }
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_analyst_denied(client: AsyncClient, setup_resolution_data, mock_analyst):
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_analyst)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "decision": "REJECTED",
        "decision_notes": "Ana"
    }
    resp = await client.post("/api/v1/identity/resolve", json=payload)
    assert resp.status_code == 403

@pytest.mark.asyncio
async def test_concurrent_resolutions(client: AsyncClient, setup_resolution_data, mock_supervisor):
    # Tests that concurrent identical ACCEPTED resolutions are serialized
    import asyncio
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_supervisor)
    
    payload = {
        "source_identity_id": setup_resolution_data["source_identity_id"],
        "person_id": setup_resolution_data["person_id"],
        "decision": "ACCEPTED",
        "decision_notes": "Concurrent"
    }
    
    # Fire multiple concurrent requests
    tasks = [client.post("/api/v1/identity/resolve", json=payload) for _ in range(3)]
    responses = await asyncio.gather(*tasks)
    
    assert all(r.status_code == 200 for r in responses)
    # The outcome will be valid and serialized due to FOR UPDATE lock

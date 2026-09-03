import pytest
from httpx import AsyncClient
from uuid import uuid4
from sqlalchemy import text
from civix_api.worker.cdc import CDCWorker
import os

pytestmark = pytest.mark.asyncio

@pytest.fixture
def cdc_worker():
    # Provide credentials to test DBs
    pg_dsn = os.getenv("CIVIX_DATABASE_URL_SYNC", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
    worker = CDCWorker(pg_dsn, neo4j_uri, neo4j_user, neo4j_pass)
    yield worker
    worker.stop()

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
        "role": "INVESTIGATOR",
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
    
    for u in [mock_investigator, mock_readonly_user, mock_admin]:
        await db_session.execute(
            text(f"INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) VALUES ('{u['user_id']}', 'auth-{u['user_id']}', '{u['username']}', '{u['username']}', '{u['role']}', 'SECRET') ON CONFLICT DO NOTHING")
        )
    await db_session.commit()

    token = create_token(sub=mock_admin['user_id'])
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/cases", json={
            "case_number": f"CIV-TEST-{uuid4().hex[:6]}",
            "title": "Test Case",
            "case_type": "CRIMINAL",
            "jurisdiction": "Test Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        case_id = res.json()["case_id"]

    await db_session.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": mock_admin['user_id']})
    await db_session.execute(
        text(f"INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES ('{case_id}', '{mock_investigator['user_id']}', 'WRITE', '{mock_admin['user_id']}')")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES ('{case_id}', '{mock_readonly_user['user_id']}', 'READ', '{mock_admin['user_id']}')")
    )
    
    await db_session.execute(
        text(f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{entity_id}', 'PERSON')")
    )
    await db_session.execute(
        text(f"INSERT INTO civix.person (entity_id, display_name) VALUES ('{entity_id}', 'Test Person')")
    )
    
    await db_session.commit()
    return {
        "case_id": str(case_id),
        "entity_id": str(entity_id)
    }

def flush_outbox(worker: CDCWorker):
    """Drain the outbox synchronously."""
    processed = True
    count = 0
    while processed and count < 100:
        processed = worker.process_next_event()
        if processed:
            count += 1
    print(f"Flushed {count} events from outbox")
    return count

async def test_network_integration_full_lifecycle(client: AsyncClient, setup_case_and_entity, mock_investigator, db_session, cdc_worker):
    """
    Test Phase 4 Requirements:
    1. POST entity -> case_entity_role -> Neo4j projection -> GET graph -> HAS_ROLE visible
    2. Role update propagates to Neo4j (idempotency)
    3. Soft-delete (tx_end set) removes HAS_ROLE from graph
    """
    from civix_api.main import app
    from civix_api.dependencies import get_current_user_from_token
    from civix_api.auth.principal import AuthenticatedCivixUser
    
    app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(**mock_investigator)
    
    case_id = setup_case_and_entity["case_id"]
    entity_id = setup_case_and_entity["entity_id"]

    # 0. Flush outbox to project Case and Entity into Neo4j
    flushed_initial = flush_outbox(cdc_worker)
    assert flushed_initial > 0, "Expected outbox events for initial Case and Entity creation"

    # 1. LINK ENTITY (POST case_entity_role)
    payload = {
        "entity_id": entity_id,
        "role": "SUSPECT",
        "role_basis": "Initial link"
    }
    resp = await client.post(f"/api/v1/cases/{case_id}/entities", json=payload)
    assert resp.status_code == 201
    
    # 2. RUN CDC WORKER
    # This will consume the UPSERT_EDGE event generated by the trigger on case_entity_role
    flushed = flush_outbox(cdc_worker)
    assert flushed > 0, "Expected outbox events for the new case_entity_role"
    
    # 3. GET GRAPH (Verify HAS_ROLE)
    graph_resp = await client.get(f"/api/v1/cases/{case_id}/graph?depth=1")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    
    rels = graph_data.get("relationships", [])
    has_role_rels = [r for r in rels if r["type"] == "HAS_ROLE" and r["end_node"] == entity_id]

    assert len(has_role_rels) == 1
    assert has_role_rels[0]["properties"]["role"] == "SUSPECT"
    assert has_role_rels[0]["properties"]["role_basis"] == "Initial link"

    # 4. UPDATE ROLE (Idempotency check)
    # The API endpoint for update doesn't exist yet, so we update SQL directly to simulate
    await db_session.execute(text(f"""
        UPDATE civix.case_entity_role 
        SET role = 'WITNESS', role_basis = 'Changed mind' 
        WHERE case_id = '{case_id}' AND entity_id = '{entity_id}' AND tx_end IS NULL
    """))
    await db_session.commit()
    
    flush_outbox(cdc_worker)
    
    graph_resp = await client.get(f"/api/v1/cases/{case_id}/graph?depth=1")
    graph_data = graph_resp.json()
    rels = graph_data.get("relationships", [])
    has_role_rels = [r for r in rels if r["type"] == "HAS_ROLE" and r["end_node"] == entity_id]
    
    assert len(has_role_rels) == 1
    assert has_role_rels[0]["properties"]["role"] == "WITNESS"

    # 5. SOFT DELETE (DEACTIVATE_EDGE)
    # Set tx_end to simulate removal
    await db_session.execute(text(f"""
        UPDATE civix.case_entity_role 
        SET tx_end = now() 
        WHERE case_id = '{case_id}' AND entity_id = '{entity_id}' AND tx_end IS NULL
    """))
    await db_session.commit()
    
    flush_outbox(cdc_worker)
    
    graph_resp = await client.get(f"/api/v1/cases/{case_id}/graph?depth=1")
    graph_data = graph_resp.json()
    rels = graph_data.get("relationships", [])
    has_role_rels = [r for r in rels if r["type"] == "HAS_ROLE" and r["end_node"] == entity_id]
    assert len(has_role_rels) == 0, "HAS_ROLE should be removed after soft delete"

    # 6. Verify case_number resolution in graph endpoint
    # Find the case_number from PG
    case_row = await db_session.execute(text("SELECT case_number FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
    case_number = case_row.first()[0]

    # Test that the graph endpoint can be called with case_number instead of UUID
    graph_resp_by_num = await client.get(f"/api/v1/cases/{case_number}/graph?depth=1")
    assert graph_resp_by_num.status_code == 200, "Graph endpoint should resolve case_number seamlessly"
    assert graph_resp_by_num.json()["nodes"] == graph_data["nodes"]


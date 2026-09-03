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
        "role": "INVESTIGATOR",
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_scenario_cross_case_isolation(db_session, create_test_user):
    # Scenario A & B: Cross-case enumeration
    user_a = await create_test_user()
    user_b = await create_test_user()
    token_a = create_token(str(user_a))
    token_b = create_token(str(user_b))

    # Create cases via API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_a = await ac.post("/api/v1/cases", json={"case_number": f"CA-{uuid4().hex[:6]}", "title": "Case A", "case_type": "CRIMINAL", "jurisdiction": "A"}, headers={"Authorization": f"Bearer {token_a}"})
        case_a_id = res_a.json()["case_id"]

        res_b = await ac.post("/api/v1/cases", json={"case_number": f"CB-{uuid4().hex[:6]}", "title": "Case B", "case_type": "CRIMINAL", "jurisdiction": "B"}, headers={"Authorization": f"Bearer {token_b}"})
        case_b_id = res_b.json()["case_id"]

        # Create source
        source_id = str(uuid4())
        await db_session.execute(text(f"INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score) VALUES (:s, 'Src1-{uuid4().hex[:6]}', 'TELECOM', 0.9)"), {"s": source_id})
        await db_session.commit()

        # User A Ingests CDR
        ext_ref = f"CDR-{uuid4()}"
        caller_num = f"555{str(uuid4().int)[:7]}"
        res_ingest = await ac.post(f"/api/v1/cases/{case_a_id}/ingest/cdr", headers={"Authorization": f"Bearer {token_a}"}, json={
            "source_id": source_id,
            "records": [{"external_reference": ext_ref, "caller_identifier": caller_num, "callee_identifier": "5559999999", "timestamp": datetime.utcnow().isoformat()}]
        })
        assert res_ingest.status_code == 200

        # Get entity ID directly from DB
        db_res = await db_session.execute(text("SELECT entity_id FROM civix.source_identity WHERE raw_identifier = :m"), {"m": caller_num})
        entity_id = str(db_res.scalar())

        # User B attempts to retrieve entity
        res_get_b = await ac.get(f"/api/v1/entities/{entity_id}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_get_b.status_code == 404, f"Scenario A Failed: Entity retrieved by User B. Status: {res_get_b.status_code}"

        # User B attempts to search entity
        res_search_b = await ac.get(f"/api/v1/search?q={caller_num}", headers={"Authorization": f"Bearer {token_b}"})
        assert res_search_b.status_code == 200
        assert len(res_search_b.json().get("results", [])) == 0, f"Scenario B Failed: Search leaked entity to User B. {res_search_b.json()}"

@pytest.mark.asyncio
async def test_scenario_tombstone_isolation(db_session, create_test_user):
    user_a = await create_test_user()
    token_a = create_token(str(user_a))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_a = await ac.post("/api/v1/cases", json={"case_number": f"CD-{uuid4().hex[:6]}", "title": "Case D", "case_type": "CRIMINAL", "jurisdiction": "D"}, headers={"Authorization": f"Bearer {token_a}"})
        case_a_id = res_a.json()["case_id"]

        entity_id = str(uuid4())
        await db_session.execute(text("INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES (:e, 'PERSON', 'ACTIVE')"), {"e": entity_id})
        await db_session.execute(text("INSERT INTO civix.person (entity_id, display_name, is_deceased) VALUES (:e, 'Tombstoned Entity', false)"), {"e": entity_id})
        # Note: In ADR-033/034 tombstoning is typically done via entity visibility_status or specific application logic. Let's just set visibility_status = 'TOMBSTONED'
        await db_session.execute(text("UPDATE civix.entity SET visibility_status = 'TOMBSTONED' WHERE entity_id = :e"), {"e": entity_id})
        await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a)})
        await db_session.execute(text("INSERT INTO civix.case_entity_role (case_id, entity_id, role) VALUES (:c, :e, 'SUSPECT')"), {"c": case_a_id, "e": entity_id})
        await db_session.execute(text("SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"))
        await db_session.commit()

        # Retrieve
        res_get = await ac.get(f"/api/v1/entities/{entity_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert res_get.status_code == 404, "Scenario D Failed: Retrieved tombstoned entity."

        # Search
        res_search = await ac.get("/api/v1/search?q=Tombstoned%20Entity", headers={"Authorization": f"Bearer {token_a}"})
        assert len(res_search.json().get("results", [])) == 0, "Scenario D Failed: Search leaked tombstoned entity."

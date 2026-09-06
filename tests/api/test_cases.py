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

@pytest.mark.asyncio
async def test_create_case(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    case_payload = {
        "case_number": f"TEST-{uuid4().hex[:6]}",
        "title": "Test Case Title",
        "case_type": "CRIMINAL",
        "jurisdiction": "Test Jurisdiction"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/cases",
            json=case_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "case_id" in data
    assert data["case_number"] == case_payload["case_number"]

    # Verify case_access created and assigned to JWT user
    case_id = data["case_id"]
    await db_session.execute(text("RESET ROLE"))
    access_res = await db_session.execute(
        text("SELECT user_id, permission_level FROM civix.case_access WHERE case_id = :cid"),
        {"cid": case_id}
    )
    access_rows = access_res.fetchall()
    assert len(access_rows) == 1
    assert str(access_rows[0][0]) == str(user_id)
    assert access_rows[0][1] == "ADMIN"
    
    # Cleanup
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
    await db_session.commit()

@pytest.mark.asyncio
async def test_case_list_and_get_isolated(db_session, create_test_user):
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

    # User B creates a case
    case_b_num = f"CB-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_b = await ac.post("/api/v1/cases", json={
            "case_number": case_b_num, "title": "Case B", "case_type": "CRIMINAL", "jurisdiction": "Jur B"
        }, headers={"Authorization": f"Bearer {token_b}"})
        case_b_id = res_b.json()["case_id"]

    # List for User A
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_a = await ac.get("/api/v1/cases", headers={"Authorization": f"Bearer {token_a}"})
        cases_a = list_a.json()
        assert len([c for c in cases_a if c["case_id"] == case_a_id]) == 1
        assert len([c for c in cases_a if c["case_id"] == case_b_id]) == 0
        
        # Get case A for User A
        get_a_valid = await ac.get(f"/api/v1/cases/{case_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert get_a_valid.status_code == 200

        # Get case B for User A -> 404 Not Found (RLS isolated)
        get_a_invalid = await ac.get(f"/api/v1/cases/{case_b_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert get_a_invalid.status_code == 404
        
    # Cleanup
    # Case A cleanup
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a)})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :ca"), {"ca": case_a_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :ca"), {"ca": case_a_id})
    
    # Case B cleanup
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_b)})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cb"), {"cb": case_b_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cb"), {"cb": case_b_id})
    await db_session.commit()

@pytest.mark.asyncio
async def test_case_creation_failure_rollback(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    # We will trigger a database error on investigative_case insertion by causing a CHECK constraint or NOT NULL violation.
    # The title is technically NOT NULL in DB, but the API requires it. Let's send a bad case_type instead which will fail enum cast, or duplicate case_number.
    
    # Let's create one successfully
    case_num = f"DUP-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "Valid Case", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        assert res1.status_code == 200
        case_1_id = res1.json()["case_id"]
        
        # Attempt to create another with the exact same case_number (which has a UNIQUE constraint)
        # This will fail on the `investigative_case` insert.
        res2 = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "Dup Case", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 409  # Handled sqlalchemy IntegrityError is a 409, which rolls back

    # Verify no orphaned case_access rows were created for the failed request
    await db_session.execute(text("RESET ROLE"))
    access_res = await db_session.execute(
        text("SELECT case_id FROM civix.case_access WHERE user_id = :uid"),
        {"uid": user_id}
    )
    rows = access_res.fetchall()
    # Should only have 1 (the valid case)
    assert len(rows) == 1
    assert str(rows[0][0]) == case_1_id

    # Cleanup
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_id)})
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_1_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_1_id})
    await db_session.commit()

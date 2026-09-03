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
async def test_hypothesis_creation_and_listing(db_session, create_test_user):
    user_a = await create_test_user()
    user_b = await create_test_user()
    
    token_a = create_token(sub=str(user_a))
    token_b = create_token(sub=str(user_b))
    
    # 1. User A creates a case
    case_num = f"CA-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "Case Hypo Test", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token_a}"})
        case_id = res.json()["case_id"]

    # 2. User A creates a hypothesis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        hypo_res = await ac.post(f"/api/v1/cases/{case_id}/hypotheses", json={
            "hypothesis_text": "The suspect fled on foot"
        }, headers={"Authorization": f"Bearer {token_a}"})
        
        assert hypo_res.status_code == 200, hypo_res.text
        data = hypo_res.json()
        assert data["hypothesis_text"] == "The suspect fled on foot"
        assert data["status"] == "ACTIVE"
        assert data["created_by"] == str(user_a)
        hypo_id = data["hypothesis_id"]

    # 3. User B tries to read the hypotheses (Unauthorized)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        read_b = await ac.get(f"/api/v1/cases/{case_id}/hypotheses", headers={"Authorization": f"Bearer {token_b}"})
        assert read_b.status_code == 404

    # 4. User B tries to create a hypothesis for User A's case (Unauthorized)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        create_b = await ac.post(f"/api/v1/cases/{case_id}/hypotheses", json={
            "hypothesis_text": "Should not work"
        }, headers={"Authorization": f"Bearer {token_b}"})
        assert create_b.status_code == 404

    # 5. User A reads hypotheses
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        read_a = await ac.get(f"/api/v1/cases/{case_id}/hypotheses", headers={"Authorization": f"Bearer {token_a}"})
        assert read_a.status_code == 200
        list_data = read_a.json()
        assert len(list_data) == 1
        assert list_data[0]["hypothesis_id"] == hypo_id

    # 6. (Skipped: No explicit audit trigger for hypothesis in this phase)

    # 7. Test Bitemporal behavior: manual soft delete / archiving
    await db_session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a)})
    await db_session.execute(text("UPDATE civix.hypothesis SET tx_end = now() WHERE hypothesis_id = :hid"), {"hid": hypo_id})
    await db_session.commit()

    # User A lists again - should be empty because tx_end IS NOT NULL
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        read_a_archived = await ac.get(f"/api/v1/cases/{case_id}/hypotheses", headers={"Authorization": f"Bearer {token_a}"})
        assert read_a_archived.status_code == 200
        assert len(read_a_archived.json()) == 0

    # Cleanup is handled by conftest.py which will safely skip cases containing immutable hypotheses.

import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.config import settings

def create_token(sub: str, exp_delta: int = 3600) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=exp_delta)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_auth_missing_header():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_malformed_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": "Bearer malformed.token.here"})
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_invalid_signature():
    token = jwt.encode({"sub": str(uuid4()), "exp": datetime.utcnow() + timedelta(hours=1)}, "wrong_secret", algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_expired_token():
    token = create_token(sub=str(uuid4()), exp_delta=-3600)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_auth_missing_sub():
    payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Missing 'sub' claim" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_invalid_uuid():
    token = create_token(sub="not-a-uuid")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "valid UUID" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_user_not_found():
    # Valid UUID but not in DB
    token = create_token(sub=str(uuid4()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_valid_token(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user_id)
    assert data["username"].startswith("user_")

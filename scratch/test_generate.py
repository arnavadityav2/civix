import asyncio
import jwt
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from civix_api.main import app
from civix_api.config import settings
import asyncpg

async def run():
    DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'
    conn = await asyncpg.connect(DB_DSN)
    case_id = await conn.fetchval("SELECT case_id FROM civix.investigative_case WHERE title = 'Golden Case 001'")
    
    # 1. create test user
    import uuid
    test_user_id = str(uuid.uuid4())
    username = f"c4_tester_{test_user_id[:8]}"
    
    await conn.execute(
        '''INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, is_active)
           VALUES ($1, $2, $3, $4, 'INVESTIGATOR', true)''',
        test_user_id, f"auth-{test_user_id}", username, "C4 Test Investigator"
    )
    
    await conn.execute(
        '''INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by, granted_at)
           VALUES ($1, $2, 'WRITE', $2, NOW())''',
        case_id, test_user_id
    )
    
    payload = {
        "sub": test_user_id,
        "role": "INVESTIGATOR",
        "exp": datetime.utcnow() + timedelta(hours=2),
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        resp = await c.post(f"/api/v1/cases/{case_id}/leads/generate", json={}, headers=headers)
        print("Status:", resp.status_code)
        print("Response:", resp.json())
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(run())

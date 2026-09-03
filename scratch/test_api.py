import asyncio, asyncpg
import urllib.request, urllib.error, jwt
from datetime import datetime, timedelta, timezone

async def test():
    conn = await asyncpg.connect('postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test')
    user = await conn.fetchrow('SELECT user_id, username, role FROM civix.civix_user LIMIT 1')
    if not user:
        print('No users in DB!')
        return
    uid, username, role = user['user_id'], user['username'], user['role']
    await conn.close()
    
    payload = {
        'sub': str(uid),
        'email': f'{username}@civix.com',
        'role': role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, 'test_secret', algorithm='HS256')
    
    # Test 1: with cvx-077-455
    req1 = urllib.request.Request('http://localhost:8000/api/v1/cases/cvx-077-455/graph?depth=1', headers={'Authorization': f'Bearer {token}'})
    try:
        print("Testing GET /api/v1/cases/cvx-077-455/graph?depth=1")
        with urllib.request.urlopen(req1) as response:
            print(f"HTTP {response.status}")
            print(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code} - {e.read().decode()}')

    # Test 2: checking the case list API
    req2 = urllib.request.Request('http://localhost:8000/api/v1/cases', headers={'Authorization': f'Bearer {token}'})
    try:
        print("\nTesting GET /api/v1/cases")
        with urllib.request.urlopen(req2) as response:
            print(f"HTTP {response.status}")
            print(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f'HTTP Error: {e.code} - {e.read().decode()}')

asyncio.run(test())

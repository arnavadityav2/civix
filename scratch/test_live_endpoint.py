import asyncio
import jwt
from datetime import datetime, timedelta, timezone
import httpx
from civix_api.config import settings

async def test_live_http():
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        resp = await client.get("/api/v1/cases/registry?page=1&page_size=50", headers=headers)
        print("Status code:", resp.status_code)
        if resp.status_code == 200:
            print("Successfully received case registry response! Items count:", len(resp.json()["items"]))
        else:
            print("Error response:", resp.text)

if __name__ == "__main__":
    asyncio.run(test_live_http())

import asyncio
from httpx import AsyncClient, ASGITransport
from civix_api.main import app

async def test_cctv_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        # We need a token. We can spoof it using the test JWT trick.
        # First let's just get the health
        resp = await c.get("/health")
        print(f"Health: {resp.status_code}")
        
        # Test /cctv/cameras without token (should be 401)
        resp = await c.get("/api/v1/cctv/cameras")
        print(f"Cameras without auth: {resp.status_code}")
        
if __name__ == "__main__":
    asyncio.run(test_cctv_endpoints())

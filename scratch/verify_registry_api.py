import asyncio
import httpx
import jwt
from datetime import datetime, timedelta, timezone

SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"

def create_dev_token():
    payload = {
        "sub": "55284c17-1d58-461f-94f5-86c2a5215100",
        "user_id": "55284c17-1d58-461f-94f5-86c2a5215100",
        "email": "investigator@civix.gov.in",
        "roles": ["INVESTIGATOR", "ANALYST"],
        "clearance_level": "TOP_SECRET",
        "jurisdiction": "DELHI",
        "exp": datetime.now(timezone.utc) + timedelta(hours=2)
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")

async def main():
    token = create_dev_token()
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        res = await client.get("http://localhost:8000/api/v1/cases/registry?page=1&page_size=10", headers=headers)
        print("Registry API Status:", res.status_code)
        if res.status_code == 200:
            data = res.json()
            items = data.get("items", [])
            print(f"Total Registry Items Returned: {len(items)}\n")
            for i, item in enumerate(items[:10], 1):
                print(f"{i:2d}. [{item['case_number']}] {item['title']} | Priority: {item['priority']} | Provenance: {item['provenance']}")
        else:
            print("Error:", res.text)

if __name__ == "__main__":
    asyncio.run(main())

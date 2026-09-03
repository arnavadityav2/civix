import sys
sys.path.insert(0, ".")

import httpx
import asyncio
import jwt
from uuid import UUID
from datetime import datetime, timezone, timedelta
from civix_api.config import settings

BASE_URL = "http://127.0.0.1:8000"

def create_jwt(user_id: str) -> str:
    payload = {"sub": user_id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)}
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

async def test_input_attacks():
    import psycopg2
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1;")
    admin_uid = str(cur.fetchone()[0])
    conn.close()

    token = create_jwt(admin_uid)
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        print("=== INPUT ATTACK TEST 1: MALFORMED BBOX STRINGS ===")
        bad_bboxes = [
            "abc,def,ghi,jkl",
            "76.8,28.3,77.4",
            "181.0,28.3,77.4,28.9",
            "76.8,28.3,77.4,28.3", # min_lat == max_lat
            "77.4,28.3,76.8,28.9", # min_lon > max_lon
            "76.8,28.3; DROP TABLE civix.location;--,77.4,28.9"
        ]
        for b in bad_bboxes:
            r = await client.get(f"/api/v1/spatial/cases?bbox={b}", headers=headers)
            print(f"  bbox='{b:<45}' -> Status: {r.status_code} | Detail: {r.json().get('detail')}")
            assert r.status_code == 400

        print("\n=== INPUT ATTACK TEST 2: INVALID LIMIT / PARAMS ===")
        limits = [-1, 0, 10000, "abc"]
        for l in limits:
            r = await client.get(f"/api/v1/spatial/cases?limit={l}", headers=headers)
            print(f"  limit='{l}' -> Status: {r.status_code}")

        print("\n=== INPUT ATTACK TEST 3: MALFORMED / NON-EXISTENT CASE UUID ===")
        bad_uuids = [
            "not-a-uuid",
            "00000000-0000-0000-0000-000000000000",
        ]
        for u in bad_uuids:
            r = await client.get(f"/api/v1/spatial/cases/{u}/events", headers=headers)
            print(f"  case_id='{u:<45}' -> Status: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(test_input_attacks())

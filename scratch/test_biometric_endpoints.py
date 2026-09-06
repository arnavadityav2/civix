import os
import sys
sys.path.insert(0, os.path.abspath("."))

import time
import jwt
import httpx
import json
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def generate_token():
    engine = create_async_engine(settings.civix_database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT user_id, username FROM civix.civix_user LIMIT 1"))
        row = res.first()
        user_id, username = str(row[0]), row[1]
        print(f"Found User: {username} ({user_id})")

    payload = {
        "sub": user_id,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    print(f"Generated Token: {token[:20]}...")

    headers = {"Authorization": f"Bearer {token}"}
    client = httpx.Client(base_url="http://127.0.0.1:8000", headers=headers, timeout=10.0)

    # 1. Health check
    res = client.get("/health")
    print("\nHealth:", res.status_code, res.json())

    # 2. Case Biometric Manifest for CIV-2012-001
    res = client.get("/api/v1/cases/CIV-2012-001/biometric-manifest")
    print("\nCIV-2012-001 Biometric Manifest:", res.status_code)
    if res.status_code == 200:
        data = res.json()
        print(f"  Case ID: {data.get('case_id')}, Title: {data.get('case_title')}")
        print(f"  Total Persons: {data.get('total_persons')}, Available: {data.get('biometric_available_count')}")
        for p in data.get("persons", []):
            print(f"    - {p['display_name']} ({p['primary_role']}): Biometric {'AVAILABLE' if p['biometric_available'] else 'UNAVAILABLE'} (Refs: {p['reference_count']})")
    else:
        print("  Error:", res.text)

    # 3. Availability check for Suresh Valmiki (637038f4-633f-8457-6de9-b7142bc10381)
    suresh_id = "637038f4-633f-8457-6de9-b7142bc10381"
    res = client.get(f"/api/v1/biometric/availability/{suresh_id}")
    print(f"\nAvailability for Suresh Valmiki ({suresh_id}):", res.status_code)
    if res.status_code == 200:
        print(" ", res.json())

    # 4. Availability check for non-enrolled person
    res = client.get("/api/v1/biometric/availability/00000000-0000-0000-0000-000000000000")
    print("\nAvailability for non-enrolled ID:", res.status_code)
    if res.status_code == 200:
        print(" ", res.json())

    # 5. Batch Availability check
    res = client.post("/api/v1/biometric/batch-availability", json={"person_ids": [suresh_id, "00000000-0000-0000-0000-000000000000"]})
    print("\nBatch Availability:", res.status_code)
    if res.status_code == 200:
        print(" ", res.json())

    # 6. CCTV Trace for Suresh Valmiki
    res = client.get(f"/api/v1/biometric/cctv-trace/{suresh_id}")
    print(f"\nCCTV Trace for Suresh Valmiki:", res.status_code)
    if res.status_code == 200:
        print(" ", res.json())

    # 7. Person Summary for Suresh Valmiki
    res = client.get(f"/api/v1/biometric/person-summary/{suresh_id}")
    print(f"\nPerson Summary for Suresh Valmiki:", res.status_code)
    if res.status_code == 200:
        data = res.json()
        print(f"  Name: {data.get('display_name')}")
        print(f"  Linked Cases: {len(data.get('linked_cases', []))}")
        print(f"  Evidence: {len(data.get('evidence', []))}")
        print(f"  Events: {len(data.get('events', []))}")

    # 8. Test Search Endpoint with a reference image
    ref_img_path = r"C:\data\civix_demo\biometric_demo\references\637038f4-633f-8457-6de9-b7142bc10381_ref_01.jpg"
    if os.path.exists(ref_img_path):
        with open(ref_img_path, "rb") as f:
            files = {"file": ("test.jpg", f, "image/jpeg")}
            res = client.post("/api/v1/biometric/search", files=files)
            print(f"\nSearch with Suresh Valmiki ref image:", res.status_code)
            if res.status_code == 200:
                print("  Result:", json.dumps(res.json(), indent=2))
            else:
                print("  Error:", res.text)
    else:
        print(f"\nReference image not found at {ref_img_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(generate_token())

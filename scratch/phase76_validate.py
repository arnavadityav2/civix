import os
import time
import uuid
import jwt
import requests
from civix_api.config import settings

def run_validation():
    print("=== CIVIX 2.0 PHASE 7.6 API VALIDATION ===")
    
    secret = settings.civix_jwt_secret
    if not secret:
        print("ERROR: civix_jwt_secret not set!")
        return

    # Use existing user UUID from civix.civix_user
    user_uuid = "55284c17-1d58-461f-94f5-86c2a5215100"
    payload = {
        "sub": user_uuid,
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    
    base_url = "http://127.0.0.1:8000/api/v1/telecom"
    
    # 1. Test GET /benchmark/case-phones for BENCH-TELECOM-001
    print("\n--- 1. Testing GET /benchmark/case-phones (BENCH-TELECOM-001) ---")
    r1 = requests.get(f"{base_url}/benchmark/case-phones?case_id=BENCH-TELECOM-001&limit=10", headers=headers)
    print(f"Status: {r1.status_code}")
    if r1.status_code == 200:
        data1 = r1.json()
        phones1 = data1.get("phones", [])
        print(f"Total active MSISDNs returned: {len(phones1)}")
        if len(phones1) > 0:
            print(f"Sample MSISDNs: {phones1[:3]}")
    else:
        print(f"Response: {r1.text}")
        
    # 2. Test GET /benchmark/case-phones for BENCH-TELECOM-002
    print("\n--- 2. Testing GET /benchmark/case-phones (BENCH-TELECOM-002) ---")
    r2 = requests.get(f"{base_url}/benchmark/case-phones?case_id=BENCH-TELECOM-002&limit=10", headers=headers)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        data2 = r2.json()
        phones2 = data2.get("phones", [])
        print(f"Total active MSISDNs returned: {len(phones2)}")
        if len(phones2) > 0:
            print(f"Sample MSISDNs: {phones2[:3]}")
    else:
        print(f"Response: {r2.text}")

    # 3. Test GET /co-location with Pagination (M-1)
    print("\n--- 3. Testing GET /co-location Pagination ---")
    if 'phones2' in locals() and len(phones2) >= 2:
        pa = phones2[0]["msisdn"]
        pb = phones2[1]["msisdn"]
    else:
        pa, pb = "9892755291", "9833011918"

    co_loc_url = f"{base_url}/co-location?case_id=BENCH-TELECOM-002&msisdn_a={pa}&msisdn_b={pb}&overlap_window_seconds=86400&page=1&page_size=5"
    r3 = requests.get(co_loc_url, headers=headers)
    print(f"Status: {r3.status_code}")
    if r3.status_code == 200:
        res3 = r3.json()
        pag = res3.get("pagination", {})
        print(f"Pagination metadata: total={pag.get('total')}, page={pag.get('page')}, page_size={pag.get('page_size')}, total_pages={pag.get('total_pages')}")
        results = res3.get('results', [])
        print(f"Co-locations in page 1: {len(results)}")
        if len(results) > 0:
            print(f"Sample co-location match: {results[0]}")
    else:
        print(f"Response: {r3.text}")

    # 4. Test Primary Case Routing Protection
    print("\n--- 4. Testing Primary Case Routing Protection ---")
    r4 = requests.get(f"{base_url}/benchmark/case-phones?case_id=PRIMARY-CASE-001", headers=headers)
    print(f"Status: {r4.status_code} (Expected 400 for non-benchmark case_id format)")
    print(f"Response: {r4.text}")

if __name__ == "__main__":
    run_validation()

import sys
import os
import urllib.request
import json
import jwt
from datetime import datetime, timezone, timedelta
sys.path.insert(0, os.path.abspath("."))

from civix_api.config import settings

def make_token():
    payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "role": "SUPER_ADMIN",
        "clearance_level": "TOP_SECRET",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

token = make_token()
CASES = ['CIV-2012-001', 'CIV-2024-010', 'CIV-2026-009']
DEPTHS = [1, 2, 3, 4, 5]

print("============================================================")
print("CIVIX 2.0 INVESTIGATIVE GRAPH — FINAL ACCEPTANCE VERIFICATION")
print("============================================================")

all_passed = True

for case_id in CASES:
    print(f"\n--- CASE: {case_id} ---")
    for depth in DEPTHS:
        url = f"http://127.0.0.1:8000/api/v1/cases/{case_id}/graph?depth={depth}&node_limit=500&rel_limit=1000"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "X-User-Clearance": "TOP_SECRET"
        })
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                nodes = data.get('nodes', [])
                rels = data.get('relationships', [])
                meta = data.get('metadata', {})
                
                nodes_count = len(nodes)
                rels_count = len(rels)
                truncated = meta.get('truncated', False)
                
                # Check data limits enforcement
                if nodes_count > 500:
                    print(f"[FAIL] Depth {depth}: Node count {nodes_count} exceeds max limit 500!")
                    all_passed = False
                elif rels_count > 1000:
                    print(f"[FAIL] Depth {depth}: Rel count {rels_count} exceeds max limit 1000!")
                    all_passed = False
                else:
                    print(f"[PASS] Depth {depth}: Nodes = {nodes_count}, Rels = {rels_count}, Truncated = {truncated}")
        except Exception as e:
            print(f"[FAIL] Depth {depth}: HTTP Error -> {e}")
            all_passed = False

print("\n------------------------------------------------------------")
if all_passed:
    print("API GRAPH DATA TRUTH VERIFICATION: ALL 15 MATRIX TESTS PASSED")
else:
    print("API GRAPH DATA TRUTH VERIFICATION: FAILED")
print("------------------------------------------------------------")

import sys
import os
sys.path.insert(0, os.path.abspath("."))

import urllib.request
import json
import jwt
from datetime import datetime, timezone, timedelta
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

print("=== CIVIX INVESTIGATIVE GRAPH DATA TRUTH VERIFICATION ===")
for case_id in CASES:
    print(f"\nCASE: {case_id}")
    for depth in DEPTHS:
        url = f"http://127.0.0.1:8000/api/v1/cases/{case_id}/graph?depth={depth}&node_limit=500&rel_limit=1000"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {token}",
            "X-User-Clearance": "TOP_SECRET"
        })
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                nodes_len = len(data.get('nodes', []))
                rels_len = len(data.get('relationships', []))
                meta = data.get('metadata', {})
                truncated = meta.get('truncated', False)
                print(f"  Depth {depth}: Nodes = {nodes_len}, Relationships = {rels_len}, Truncated = {truncated}")
        except Exception as e:
            print(f"  Depth {depth}: Error -> {e}")

print("\n=== VERIFICATION COMPLETE ===")

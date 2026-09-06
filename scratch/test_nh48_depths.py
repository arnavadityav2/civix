import urllib.request
import json
import jwt
import time

SECRET = 'civix-dev-secret-round2-do-not-use-in-production-change-this'
ADMIN_UID = 'da319cf1-8040-4ad2-89d8-5846e1aa9e76'
CASE_ID = '1346a86d-267a-a635-9d62-e34c76ecd24f' # CIV-2012-001

token = jwt.encode({'sub': ADMIN_UID, 'exp': int(time.time()) + 3600}, SECRET, algorithm='HS256')

print("==========================================================================")
print("LIVE NEO4J BACKEND UNIVERSE EXPANSION (CIV-2012-001)")
print("==========================================================================")
for depth in range(1, 6):
    url = f"http://127.0.0.1:8000/api/v1/cases/{CASE_ID}/universe?depth={depth}"
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    res = json.loads(urllib.request.urlopen(req).read())
    nodes = res['nodes']
    rels = res['relationships']
    print(f"Depth {depth}H: {len(nodes):3d} nodes | {len(rels):3d} relationships")

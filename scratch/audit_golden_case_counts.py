import urllib.request
import json
import jwt
import time

SECRET = 'civix-dev-secret-round2-do-not-use-in-production-change-this'
ADMIN_UID = 'da319cf1-8040-4ad2-89d8-5846e1aa9e76'

with open("database/protected_hero_cases.json", "r") as f:
    manifest = json.load(f)

cases = manifest["protected_cases"]
token = jwt.encode({'sub': ADMIN_UID, 'exp': int(time.time()) + 3600}, SECRET, algorithm='HS256')

results = []

print("==========================================================================")
print("AUDITING GRAPH NODE & RELATIONSHIP COUNTS FOR ALL 13 GOLDEN CASES")
print("==========================================================================")

for c in cases:
    cid = c["case_id"]
    cnum = c["case_number"]
    title = c["title"]
    
    url = f"http://127.0.0.1:8000/api/v1/cases/{cid}/graph?depth=2&node_limit=250&rel_limit=500"
    try:
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
        res = json.loads(urllib.request.urlopen(req).read())
        nodes = res.get('nodes', [])
        rels = res.get('relationships', [])
        
        # Categorize nodes
        entities = [n for n in nodes if not any(l in ['Case', 'Evidence', 'Event'] for l in n['labels'])]
        evidence = [n for n in nodes if 'Evidence' in n['labels']]
        events = [n for n in nodes if 'Event' in n['labels']]
        
        results.append({
            "case_id": cid,
            "case_number": cnum,
            "title": title,
            "total_nodes": len(nodes),
            "total_rels": len(rels),
            "entities": len(entities),
            "evidence": len(evidence),
            "events": len(events)
        })
    except Exception as e:
        results.append({
            "case_id": cid,
            "case_number": cnum,
            "title": title,
            "error": str(e)
        })

# Sort by total nodes descending
results.sort(key=lambda x: x.get("total_nodes", 0), reverse=True)

for i, r in enumerate(results):
    if "error" in r:
        print(f"{i+1:2d}. {r['case_number']:15s} | ERROR: {r['error']}")
    else:
        print(f"{i+1:2d}. {r['case_number']:15s} | Nodes: {r['total_nodes']:3d} (Entities: {r['entities']:2d}, Evidence: {r['evidence']:2d}, Events: {r['events']:2d}) | Rels: {r['total_rels']:3d} | Title: {r['title']}")

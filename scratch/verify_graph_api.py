import urllib.request
import json

headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTA5MzYzMjEsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.QdaM3wTt128IreRRdHDqxjPWkBkiuQcjVbZ7r5Fc8Ms'}

case_id = "530831f5-4032-4533-be70-8a78bb5a7435"

for depth in [1, 2]:
    url = f"http://localhost:8000/api/v1/cases/{case_id}/graph?depth={depth}&node_limit=200&rel_limit=500"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        print(f"\n--- DEPTH {depth} API RESPONSE ---")
        print("Status code:", resp.status)
        data = json.loads(resp.read().decode())
        nodes = data.get("nodes", [])
        rels = data.get("relationships", [])
        is_truncated = data.get("is_truncated", False)
        
        print(f"Nodes count: {len(nodes)}")
        print(f"Relationships count: {len(rels)}")
        print(f"Is Truncated: {is_truncated}")
        
        node_types = set(n.get("entity_type") for n in nodes)
        print("Representative Node Types:", sorted(list(node_types)))
        
        rel_predicates = set(r.get("predicate") for r in rels)
        print("Representative Canonical Predicates:", sorted(list(rel_predicates)))
        
        if nodes:
            print("\nSample Node 0:", json.dumps(nodes[0], indent=2))
        if rels:
            print("\nSample Relationship 0:", json.dumps(rels[0], indent=2))

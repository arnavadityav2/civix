import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"
case_id = "CIV-2012-001"

endpoints = [
    f"/cases/{case_id}",
    f"/cases/{case_id}/entities",
    f"/cases/{case_id}/evidence",
    f"/cases/{case_id}/events",
    f"/cases/{case_id}/assertions",
    f"/cases/{case_id}/graph"
]

def fetch(path):
    try:
        req = urllib.request.Request(f"{base_url}{path}")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

results = {}
for ep in endpoints:
    results[ep] = fetch(ep)

with open("scratch/api_dump_CIV-2012-001.json", "w") as f:
    json.dump(results, f, indent=2)

print("Dumped API responses to scratch/api_dump_CIV-2012-001.json")

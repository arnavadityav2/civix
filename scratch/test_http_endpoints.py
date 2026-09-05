import urllib.request
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTExNTU4MTUsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.T-ELt1mq7nyaxhridugVXARndl8Qy7wZjrQ41hAc914"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

endpoints = [
    "/api/v1/cases/CIV-2012-001",
    "/api/v1/cases/CIV-2012-001/entities",
    "/api/v1/cases/CIV-2012-001/evidence",
]

for ep in endpoints:
    url = f"http://127.0.0.1:8000{ep}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"SUCCESS GET {ep}: status {resp.status}, returned {len(data) if isinstance(data, list) else 'object'} items")
            if ep.endswith("/entities"):
                print("  Entities count:", len(data))
                for ent in data:
                    print("   -", ent['display_name'], f"({ent['role']})")
            elif ep.endswith("/evidence"):
                print("  Evidence count:", len(data))
                for ev in data[:3]:
                    print("   -", ev['artifact_id'], "|", ev['original_filename'], "|", ev['evidence_type'])
    except Exception as e:
        print(f"FAILED GET {ep}:", e)

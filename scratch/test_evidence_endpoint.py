import urllib.request
import json

base_url = "http://127.0.0.1:8000"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ"
headers = {"Authorization": f"Bearer {token}"}

# 1. Fetch global evidence list
req = urllib.request.Request(f"{base_url}/api/v1/evidence", headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        items = json.loads(resp.read().decode('utf-8'))
        print(f"Total evidence items fetched: {len(items)}")
        if items:
            sample = items[0]
            print("\nSample Evidence Item:", sample)
            
            # 2. Test fetching static image from /evidence_store/{storage_uri}
            if sample.get('storage_uri'):
                img_url = f"{base_url}/evidence_store/{sample['storage_uri']}"
                img_req = urllib.request.Request(img_url)
                with urllib.request.urlopen(img_req) as img_resp:
                    img_bytes = img_resp.read()
                    print(f"Static Image URL ({img_url}) returned {len(img_bytes)} bytes!")

except Exception as e:
    print(f"Error: {e}")

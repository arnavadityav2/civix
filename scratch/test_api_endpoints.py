import urllib.request
import json

# Obtain a token using dev token generator or test directly if auth required
req = urllib.request.Request("http://127.0.0.1:8000/api/v1/cases/CIV-2012-001")
try:
    with urllib.request.urlopen(req) as resp:
        print("GET /cases/CIV-2012-001 -> Status:", resp.status)
        print("Case data:", json.loads(resp.read().decode('utf-8')))
except Exception as e:
    print("Error querying /cases/CIV-2012-001:", e)

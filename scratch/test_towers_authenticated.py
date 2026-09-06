import jwt
import time
import urllib.request
import json

secret = "civix-dev-secret-round2-do-not-use-in-production-change-this"

payload = {
    "sub": "fa06b8fa-aa1f-47ea-9f80-d5368b5915a8",
    "exp": int(time.time()) + 3600
}

token = jwt.encode(payload, secret, algorithm="HS256")

url = "http://127.0.0.1:8000/api/v1/cases/CIV-2012-001/telecom/towers"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

try:
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode('utf-8'))
    print("API Response Success!")
    print(f"Total active cell towers returned across Delhi NCR: {data.get('count')}")
    print("Sample active cell towers:")
    for t in data.get("towers", [])[:20]:
        print(f"  • {t['name']} | Lat: {t['centroid_lat']}, Lon: {t['centroid_lon']} | Hits: {t['hit_count']}")
except Exception as e:
    print("Request failed:", e)

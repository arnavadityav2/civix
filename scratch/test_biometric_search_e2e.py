import sys
sys.path.insert(0, '.')
import json
import time
import jwt
import requests
from civix_api.config import settings

payload = {
    "sub": "55284c17-1d58-461f-94f5-86c2a5215100",
    "exp": int(time.time()) + 3600
}
token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}

pid = "09d7a50a-82dd-4acf-1c8c-ed1d70f5b332"

print("--- TESTING GET REFERENCES ---")
r1 = requests.get(f"http://127.0.0.1:8000/api/v1/biometric/references/{pid}", headers=headers)
print("Status:", r1.status_code)
print(json.dumps(r1.json(), indent=2))

print("\n--- TESTING GET CONTEXT ---")
r2 = requests.get(f"http://127.0.0.1:8000/api/v1/biometric/context/{pid}", headers=headers)
print("Status:", r2.status_code)
print(json.dumps(r2.json(), indent=2))

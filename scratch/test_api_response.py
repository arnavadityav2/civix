import requests
from datetime import datetime, timezone, timedelta
import jwt

SECRET_KEY = "civix-dev-secret-round2-do-not-use-in-production-change-this"
ALGORITHM = "HS256"

# Create token for Inspector Vikram (00000000-0000-0000-0000-000000000001)
payload = {
    "sub": "00000000-0000-0000-0000-000000000001",
    "role": "SUPER_ADMIN",
    "clearance_level": 5,
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
headers = {"Authorization": f"Bearer {token}"}

url = "http://127.0.0.1:8000/api/v1/cases/CIV-2012-001/entities"
resp = requests.get(url, headers=headers)

print(f"HTTP Status: {resp.status_code}")
if resp.status_code == 200:
    entities = resp.json()
    print(f"Total entities returned: {len(entities)}")
    suresh = next((e for e in entities if e.get("display_name") == "Suresh Valmiki"), None)
    print("=== SURESH VALMIKI IN API RESPONSE ===")
    print(suresh)
else:
    print(resp.text)

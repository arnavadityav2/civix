import time
import jwt
import requests
from civix_api.config import settings

def test():
    user_id = "00000000-0000-0000-0000-000000000001"
    payload = {
        "sub": user_id,
        "role": "ADMIN",
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get("http://localhost:8000/api/v1/cases/registry", headers=headers)
    print("Registry API Status:", res.status_code)
    data = res.json()
    print("Total Cases:", data.get("summary", {}).get("total_cases"))
    print("Item Count:", len(data.get("items", [])))

if __name__ == "__main__":
    test()

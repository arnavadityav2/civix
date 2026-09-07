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

    cam_id = "c0c70025-0015-4000-8000-000000000015"
    res = requests.get(f"http://localhost:8000/api/v1/cctv/media/{cam_id}", headers=headers, stream=True)
    print("Akshardham Media Stream API Status:", res.status_code)
    print("Response JSON:", res.json())

if __name__ == "__main__":
    test()

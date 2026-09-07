import time
import jwt
import requests
from civix_api.config import settings

def test():
    # Admin Vikram Singh's UUID in civix_demo DB
    user_id = "00000000-0000-0000-0000-000000000001"
    payload = {
        "sub": user_id,
        "role": "ADMIN",
        "exp": int(time.time()) + 3600
    }
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    res = requests.get("http://localhost:8000/api/v1/spatial/cases", headers=headers)
    print("Spatial API Status:", res.status_code)
    data = res.json()
    features = data.get("features", [])
    print(f"Total Spatial Features returned: {len(features)}")

    golden = [f for f in features if f["properties"]["provenance"] == "GOLDEN" or not f["properties"]["case_number"].startswith("SYN-")]
    print(f"\nTotal Golden Cases returned on Map ({len(golden)}):")
    for g in golden:
        props = g["properties"]
        coords = g["geometry"]["coordinates"]
        print(f" - {props['case_number']}: {props['title']} | Coords: [{coords[0]:.4f}, {coords[1]:.4f}]")

if __name__ == "__main__":
    test()

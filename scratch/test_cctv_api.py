import requests
import jwt
from datetime import datetime, timezone, timedelta
import psycopg2

secret = "civix-dev-secret-round2-do-not-use-in-production-change-this"

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT user_id, role FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1;")
row = cur.fetchone()
admin_uid = str(row[0])
conn.close()

payload = {
    "sub": admin_uid,
    "role": "ADMIN",
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}
token = jwt.encode(payload, secret, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get("http://localhost:8000/api/v1/cctv/cameras", headers=headers)
print("Cameras Status:", resp.status_code)
cameras = resp.json()
print("Cameras Count:", len(cameras))

if cameras:
    cam_id = cameras[0]["camera_id"]
    detail_resp = requests.get(f"http://localhost:8000/api/v1/cctv/cameras/{cam_id}", headers=headers)
    print("Camera Detail Status:", detail_resp.status_code)
    detail = detail_resp.json()
    print("Feeds:", detail.get("feeds"))

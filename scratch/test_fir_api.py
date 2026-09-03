import jwt
import requests
from datetime import datetime, timezone, timedelta
import psycopg2

secret = "civix-dev-secret-round2-do-not-use-in-production-change-this"

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT user_id, role FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1;")
row = cur.fetchone()
admin_uid = str(row[0])
role = row[1]
conn.close()

payload = {
    "sub": admin_uid,
    "role": role,
    "exp": datetime.now(timezone.utc) + timedelta(hours=1)
}
token = jwt.encode(payload, secret, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}

resp = requests.get("http://localhost:8000/api/v1/spatial/cases/f1742012-0074-4000-8000-000000000074/events", headers=headers)
print("HTTP Status:", resp.status_code)
data = resp.json()
print("Features count:", len(data.get("features", [])))
for f in data.get("features", []):
    props = f.get("properties", {})
    geom = f.get("geometry", {})
    print(f" - [{props.get('event_type')}] {props.get('location_name')} ({props.get('location_predicate')}) @ {geom.get('coordinates')}")

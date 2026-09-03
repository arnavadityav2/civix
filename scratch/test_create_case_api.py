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

data = {
    "case_number": "20226-055",
    "title": "mall accident",
    "case_type": "COUNTERTERRORISM",
    "priority": "HIGH",
    "jurisdiction": "DELHI",
    "investigating_unit": "DELHI TASK FORCE"
}

resp = requests.post("http://localhost:8000/api/v1/cases", json=data, headers=headers)
print("Create Case API Status:", resp.status_code)
print("Response JSON:", resp.json())

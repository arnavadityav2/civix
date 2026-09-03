import jwt

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ"
secret = "civix-dev-secret-round2-do-not-use-in-production-change-this"

try:
    decoded = jwt.decode(token, secret, algorithms=["HS256"])
    print("Decoded token:", decoded)
except Exception as e:
    print("Token decode failed:", e)

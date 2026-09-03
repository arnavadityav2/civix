import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ"
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
print("Create User Case Status:", resp.status_code)
print("Response JSON:", resp.json())

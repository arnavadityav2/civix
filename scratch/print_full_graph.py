import urllib.request
import json

headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTA5MzYzMjEsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.QdaM3wTt128IreRRdHDqxjPWkBkiuQcjVbZ7r5Fc8Ms'}

case_id = "19c74342-8c66-4f3b-a993-16f139a86877"

url = f"http://localhost:8000/api/v1/cases/{case_id}/graph?depth=1&node_limit=200&rel_limit=500"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("GRAPH DATA:")
    print(json.dumps(data, indent=2))

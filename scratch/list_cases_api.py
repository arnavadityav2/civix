import urllib.request
import json

url = "http://localhost:8000/api/v1/cases"
req = urllib.request.Request(url, headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTA5MzYzMjEsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.QdaM3wTt128IreRRdHDqxjPWkBkiuQcjVbZ7r5Fc8Ms'})

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    print("Cases count:", len(data))
    for c in data:
        print(f"ID: {c.get('case_id')} | Number: {c.get('case_number')} | Title: {c.get('title')}")

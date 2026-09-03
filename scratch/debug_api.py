import urllib.request
import urllib.error
import json

url = "http://localhost:8000/api/v1/cases/530831f5-4032-4533-be70-8a78bb5a7435/graph?depth=1&node_limit=200&rel_limit=500"
req = urllib.request.Request(url, headers={'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTA5MzYzMjEsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.QdaM3wTt128IreRRdHDqxjPWkBkiuQcjVbZ7r5Fc8Ms'})
try:
    with urllib.request.urlopen(req) as response:
        print("Status:", response.status)
        print(response.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code)
    print("Reason:", e.reason)
    print("Body:", e.read().decode())
except Exception as e:
    print("Error:", e)

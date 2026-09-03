import urllib.request
import json

url = "http://localhost:8000/api/v1/cases/19c74342-8c66-4f3b-a993-16f139a86877/graph?depth=1"
headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTA5MzYzMjEsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.v_B8g7S0xYtP7S2xZ3e0W4A3Z2_b5c6d7e8f9a0b1c2'}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Nodes count: {len(data.get('nodes', []))}")
        print(f"Rels count: {len(data.get('relationships', []))}")
        if data.get('nodes'):
            print("First 3 nodes:", data['nodes'][:3])
except Exception as e:
    print("Error:", e)

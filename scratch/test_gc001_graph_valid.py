import jwt
import time
import urllib.request
import json
from civix_api.config import settings

user_id = "55284c17-1d58-461f-94f5-86c2a5215100"
payload = {
    "sub": user_id,
    "exp": int(time.time()) + 3600
}

token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

url = "http://localhost:8000/api/v1/cases/19c74342-8c66-4f3b-a993-16f139a86877/graph?depth=1"
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})

try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        print(f"Nodes count: {len(data.get('nodes', []))}")
        print(f"Rels count: {len(data.get('relationships', []))}")
        if data.get('nodes'):
            print("First node labels:", data['nodes'][0]['labels'])
except Exception as e:
    print("Error:", e)

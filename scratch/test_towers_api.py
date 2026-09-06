import urllib.request
import json

url = "http://127.0.0.1:8000/api/v1/cases/CIV-2012-001/telecom/towers"
try:
    req = urllib.request.urlopen(url)
    data = json.loads(req.read().decode('utf-8'))
    print("API returned count:", data.get("count"))
    print("Towers sample:")
    for t in data.get("towers", [])[:15]:
        print(f"  - {t['name']} (lat: {t['centroid_lat']}, lon: {t['centroid_lon']}, hits: {t['hit_count']})")
except Exception as e:
    print("API request failed:", e)

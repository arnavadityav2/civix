import urllib.request
import json

def test_registry():
    token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJleHAiOjE3OTExNTEwNjUsInJvbGUiOiJJTlZFU1RJR0FUT1IifQ.y4Yva5jtm8daVJdnI8ZkIZabVd420CZzUz5cbZ3SSB4'
    url = 'http://127.0.0.1:8000/api/v1/cases/registry?page=1&page_size=50'
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + token})
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    
    print("TOTAL ITEMS RETURNED:", len(data['items']))
    print("\nTOP 15 CASES IN REGISTRY:")
    for i, item in enumerate(data['items'][:15]):
        print(f"{i+1:2d}. [{item['provenance']}] {item['case_number']} | {item['title']}")

if __name__ == '__main__':
    test_registry()

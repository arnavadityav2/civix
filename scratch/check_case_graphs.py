import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ"
headers = {"Authorization": f"Bearer {token}"}

# 1. Fetch cases
req = urllib.request.Request(f"{base_url}/cases", headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        cases = json.loads(resp.read().decode('utf-8'))
        print(f"Total cases fetched: {len(cases)}")
        for c in cases[:10]:
            case_id = c['case_id']
            case_num = c.get('case_number', '')
            title = c.get('title', '')
            print(f"\nCase: {case_num} | ID: {case_id} | Title: {title}")
            
            # Fetch graph for this case using correct path /cases/{case_id}/graph
            g_req = urllib.request.Request(f"{base_url}/cases/{case_id}/graph", headers=headers)
            try:
                with urllib.request.urlopen(g_req) as g_resp:
                    g_data = json.loads(g_resp.read().decode('utf-8'))
                    nodes = g_data.get('nodes', [])
                    rels = g_data.get('relationships', [])
                    print(f"  Graph Nodes: {len(nodes)}, Rels: {len(rels)}")
                    if nodes:
                        print("  Sample Nodes:", [(n.get('id'), n.get('labels', []), n.get('properties', {}).get('display_name') or n.get('properties', {}).get('name')) for n in nodes[:3]])
                    if rels:
                        print("  Sample Rels:", [(r.get('start_node'), r.get('type'), r.get('end_node')) for r in rels[:3]])
            except Exception as ge:
                print(f"  Graph error: {ge}")

except Exception as e:
    print(f"Error fetching cases: {e}")

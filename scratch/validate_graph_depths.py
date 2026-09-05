import asyncio
import httpx
import json

async def run_validation():
    with open('database/protected_hero_cases.json', 'r') as f:
        hero_cases = json.load(f)

    print("=========================================")
    print("GRAPH API DEPTH VALIDATION (1-5 HOPS)")
    print("=========================================\n")

    async with httpx.AsyncClient(base_url="http://127.0.0.1:8000/api/v1", timeout=30.0) as client:
        # We need a token. We can mock it or just fetch a real one.
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ'
        headers = {"Authorization": f"Bearer {token}"}

        for case in hero_cases["protected_cases"]:
            case_id = case["case_id"]
            case_number = case["case_number"]
            print(f"Testing Case: {case_number} ({case_id})")

            for depth in range(1, 6):
                resp = await client.get(f"/cases/{case_id}/graph?depth={depth}&node_limit=500&rel_limit=1000", headers=headers)
                if resp.status_code != 200:
                    print(f"  [ERROR] Depth {depth}: {resp.status_code} - {resp.text}")
                    continue

                data = resp.json()
                nodes = len(data["nodes"])
                rels = len(data["relationships"])
                meta = data.get("metadata", {})
                trunc = meta.get("truncated", False)

                print(f"  Depth {depth}: {nodes} nodes, {rels} rels (Truncated: {trunc})")
            print()

asyncio.run(run_validation())

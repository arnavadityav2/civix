import asyncio
import httpx

async def main():
    case_id = "bb1a67a5-525b-48f8-f793-d60c23c514ca" # CIV-2026-009
    
    # Sign token
    import jwt
    from datetime import datetime, timedelta, timezone
    SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"
    token = jwt.encode({
        "sub": "55284c17-1d58-461f-94f5-86c2a5215100",
        "user_id": "55284c17-1d58-461f-94f5-86c2a5215100",
        "email": "investigator@civix.gov.in",
        "roles": ["INVESTIGATOR"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }, SECRET, algorithm="HS256")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        for depth in range(1, 6):
            url = f"http://localhost:8000/api/v1/cases/{case_id}/graph?depth={depth}&node_limit=150&rel_limit=300"
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                nodes = data.get("nodes", [])
                rels = data.get("relationships", [])
                meta = data.get("metadata", {})
                print(f"Depth {depth}H: Nodes={len(nodes):3d}, Rels={len(rels):3d} | Meta: req_depth={meta.get('requested_depth')}, returned_nodes={meta.get('nodes_returned')}")
            else:
                print(f"Depth {depth}H failed:", res.status_code, res.text)

if __name__ == "__main__":
    asyncio.run(main())

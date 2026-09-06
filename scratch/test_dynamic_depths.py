import asyncio
import httpx
import jwt
from datetime import datetime, timedelta, timezone

async def main():
    case_id = "bb1a67a5-525b-48f8-f793-d60c23c514ca" # CIV-2026-009
    
    SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"
    token = jwt.encode({
        "sub": "55284c17-1d58-461f-94f5-86c2a5215100",
        "user_id": "55284c17-1d58-461f-94f5-86c2a5215100",
        "email": "investigator@civix.gov.in",
        "roles": ["INVESTIGATOR"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }, SECRET, algorithm="HS256")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    depth_limits = {
        1: (80, 150),
        2: (180, 350),
        3: (350, 700),
        4: (600, 1200),
        5: (1000, 2000),
    }
    
    async with httpx.AsyncClient() as client:
        print("=== SCALED NODE LIMITS PER HOP DEPTH ===")
        for depth in range(1, 6):
            n_lim, r_lim = depth_limits[depth]
            url = f"http://localhost:8000/api/v1/cases/{case_id}/graph?depth={depth}&node_limit={n_lim}&rel_limit={r_lim}"
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                data = res.json()
                nodes = data.get("nodes", [])
                rels = data.get("relationships", [])
                meta = data.get("metadata", {})
                print(f"Depth {depth}H (Limit {n_lim:4d}): Returned Nodes = {len(nodes):4d}, Rels = {len(rels):4d}")
            else:
                print(f"Depth {depth}H failed: {res.status_code} | Detail: {res.text}")

if __name__ == "__main__":
    asyncio.run(main())

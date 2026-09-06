import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal
from civix_api.services.neo4j_query import Neo4jQueryService

async def audit_cases():
    print("==========================================================================")
    print("CIVIX 2.0 INVESTIGATIVE GRAPH PERFORMANCE & HOPS AUDIT")
    print("==========================================================================")
    
    cases = ["CIV-2012-001", "CIV-2024-010", "CIV-2026-009"]
    async with AsyncSessionLocal() as session:
        for cnum in cases:
            r = await session.execute(text("SELECT case_id, title FROM civix.investigative_case WHERE case_number = :cnum"), {"cnum": cnum})
            row = r.fetchone()
            if not row:
                print(f"Case {cnum} not found.")
                continue
            case_id, title = str(row[0]), row[1]
            print(f"\nCASE: {cnum} ({title}) [ID: {case_id}]")
            
            for depth in [1, 2, 3, 4, 5]:
                try:
                    res = await Neo4jQueryService.get_case_graph(
                        session=session,
                        case_id=case_id,
                        user_id="55284c17-1d58-461f-94f5-86c2a5215100",
                        user_clearance=5,
                        depth=depth,
                        node_limit=500,
                        rel_limit=1000
                    )
                    nodes_cnt = len(res["nodes"])
                    rels_cnt = len(res["relationships"])
                    truncated = res["metadata"].get("truncated", False)
                    print(f"  {depth} HOP(S): {nodes_cnt} nodes, {rels_cnt} relationships (Truncated: {truncated})")
                except Exception as e:
                    print(f"  {depth} HOP(S): Error {e}")

if __name__ == "__main__":
    asyncio.run(audit_cases())

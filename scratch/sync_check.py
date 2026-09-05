import asyncio
import asyncpg
from neo4j import GraphDatabase
import json

async def check_pg_and_neo4j():
    print("=== POSTGRESQL CASES ===")
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    pg_cases = await conn.fetch("SELECT case_id, case_number, title, case_type FROM civix.investigative_case ORDER BY created_at DESC LIMIT 20")
    print(f"Total PG cases count: {len(pg_cases)}")
    for r in pg_cases:
        print(f"  PG Case ID: {r['case_id']} | Num: {r['case_number']} | Title: {r['title']}")
    await conn.close()

    print("\n=== NEO4J CASE NODES ===")
    driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "password"))
    with driver.session() as session:
        # Check all Case nodes
        res = session.run("MATCH (c:Case) RETURN c.case_id AS cid, c.case_number AS cnum, c.title AS title LIMIT 20")
        neo_cases = list(res)
        print(f"Total Neo4j Case nodes count: {len(neo_cases)}")
        for r in neo_cases:
            print(f"  Neo4j Case ID: {r['cid']} | Num: {r['cnum']} | Title: {r['title']}")

        # Check relationships connected to any Case node
        res_rel = session.run("MATCH (c:Case)-[r]-(n) RETURN labels(c) AS cl, type(r) AS rel_type, labels(n) AS nl LIMIT 10")
        rels = list(res_rel)
        print(f"\nSample relationships attached to Case nodes: {len(rels)}")
        for r in rels:
            print(f"  {r['cl']} --[{r['rel_type']}]--> {r['nl']}")

        # Check ANY relationships in Neo4j
        res_any_rel = session.run("MATCH (a)-[r]->(b) RETURN labels(a) AS al, type(r) AS rel_type, labels(b) AS bl LIMIT 15")
        any_rels = list(res_any_rel)
        print(f"\nSample ANY relationships in Neo4j: {len(any_rels)}")
        for r in any_rels:
            print(f"  {r['al']} --[{r['rel_type']}]--> {r['bl']}")

    driver.close()

if __name__ == '__main__':
    asyncio.run(check_pg_and_neo4j())

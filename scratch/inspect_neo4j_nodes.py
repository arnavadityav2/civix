from neo4j import GraphDatabase
import json

uri = "bolt://localhost:7688"
driver = GraphDatabase.driver(uri, auth=None)

with driver.session() as session:
    # 1. Get all node labels and count
    res = session.run("MATCH (n) RETURN labels(n) AS lbls, count(n) AS cnt ORDER BY cnt DESC LIMIT 20")
    print("Node counts by label:")
    for r in res:
        print(f"  {r['lbls']}: {r['cnt']}")
        
    # 2. Check if Case nodes exist
    res = session.run("MATCH (c:Case) RETURN c LIMIT 5")
    case_nodes = [dict(r['c']) for r in res]
    print(f"\nTotal sample :Case nodes: {len(case_nodes)}")
    for c in case_nodes:
        print(" ", c)

    # 3. Check node property keys on Case nodes or any nodes
    res = session.run("MATCH (c:Case) RETURN keys(c) AS k LIMIT 1")
    for r in res:
        print("\nCase node keys:", r['k'])

    # 4. Find any Case node by case_number or case_id
    res = session.run("MATCH (c:Case) RETURN c.case_id, c.case_number, c.id, c.name LIMIT 10")
    print("\nSample Case node properties:")
    for r in res:
        print(" ", dict(r))

driver.close()

from neo4j import GraphDatabase

case_id = "1346a86d-267a-a635-9d62-e34c76ecd24f"
driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "password"))

with driver.session() as session:
    res = session.run("MATCH (c:Case {case_id: $case_id})-[r]-(n) RETURN c.case_number, type(r), labels(n), n.display_name", case_id=case_id)
    records = list(res)
    print(f"Total connected neighbors for {case_id}: {len(records)}")
    for r in records:
        print(" ", dict(r))

driver.close()

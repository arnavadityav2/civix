from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    with driver.session() as session:
        result = session.run("MATCH (c:Case) RETURN c")
        for r in result:
            print("Case node properties:", dict(r['c']))

        result = session.run("MATCH (c:Case)-[r]-(n) RETURN c.case_id as case_id, type(r) as rel, labels(n) as node_labels, n.entity_id as entity_id")
        print("\nDirect Case connections:")
        for r in result:
            print(r)

        result = session.run("MATCH (n) WHERE n.case_id IS NOT NULL RETURN labels(n) as labels, count(n) as cnt")
        print("\nNodes by case_id:")
        for r in result:
            print(r)

        result = session.run("MATCH (n) WHERE n.authorized_case_ids IS NOT NULL RETURN labels(n) as labels, count(n) as cnt")
        print("\nNodes by authorized_case_ids:")
        for r in result:
            print(r)

from neo4j import GraphDatabase
import os

def inspect_nodes():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        res = session.run("MATCH (n) RETURN labels(n) AS l, n LIMIT 10;")
        print("Sample existing Neo4j nodes:")
        for r in res:
            print("  Labels:", r["l"], "Props:", dict(r["n"]))
    driver.close()

if __name__ == "__main__":
    inspect_nodes()

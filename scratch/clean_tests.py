from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.execute_query(
        "MATCH (p:Person) WHERE p.entity_id IN ['45a956e5-dd68-46f2-93c1-3bf395badb60', 'c923c99e-a1af-4568-9da5-25818ffa7194'] DETACH DELETE p"
    )
    print("Cleaned up test nodes")

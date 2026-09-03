from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

with driver.session() as session:
    res = session.run("MATCH (n {entity_id: '57bed008-c646-4c21-9ea1-b8b43a80068a'}) RETURN labels(n)")
    print("Subject 1 Labels:", res.single()[0])
    
    res = session.run("MATCH (n {entity_id: '6bb7cd7a-0384-478e-a2c0-e1ea7006ddaf'}) RETURN labels(n)")
    print("Subject 2 Labels:", res.single()[0])

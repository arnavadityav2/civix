from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def test_cypher():
    query = """
    MERGE (i:Identity {entity_id: 'sub1'})
    MERGE (o:Person {entity_id: 'obj1'})
    MERGE (a:Assertion {assertion_id: 'a1'})
    SET a._lock = true
    WITH a, i, o, true AS should_apply
    
    OPTIONAL MATCH (a)<-[old_sub:ASSERTED_BY]-()
    OPTIONAL MATCH (a)-[old_obj:ASSERTS]->()
    WITH a, i, o, should_apply, collect(old_sub) AS old_subs, collect(old_obj) AS old_objs
    
    FOREACH (_ IN CASE WHEN should_apply THEN [1] ELSE [] END |
        FOREACH (sub IN [x IN old_subs WHERE x IS NOT NULL] | DELETE sub)
        FOREACH (obj IN [x IN old_objs WHERE x IS NOT NULL] | DELETE obj)
        SET a.val = 'new', a.last_seq_no = 2
        CREATE (i)-[:ASSERTED_BY]->(a)
        CREATE (a)-[:ASSERTS]->(o)
    )
    RETURN true AS projection_processed
    """
    
    try:
        with driver.session() as session:
            # Clean first
            session.run("MATCH (n) DETACH DELETE n")
            # Run test
            res = session.run(query).data()
            print("Result:", res)
            
            # Verify graph
            graph = session.run("MATCH (n) OPTIONAL MATCH (n)-[r]->(m) RETURN labels(n), n, type(r), labels(m), m").data()
            print("Graph:", graph)
    except Exception as e:
        print("Error:", e)
        
if __name__ == "__main__":
    test_cypher()

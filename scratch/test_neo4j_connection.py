from neo4j import GraphDatabase
import time

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password")

def verify_neo4j():
    # Retry logic to wait for Neo4j to boot
    for i in range(15):
        try:
            with GraphDatabase.driver(URI, auth=AUTH) as driver:
                with driver.session() as session:
                    # Test basic query
                    res = session.run("RETURN 1").single()
                    if res and res[0] == 1:
                        print("Neo4j connection successful!")
                        
                        # Count nodes
                        nodes = session.run("MATCH (n) RETURN count(n)").single()[0]
                        print(f"Total nodes: {nodes}")
                        
                        # Count relationships
                        rels = session.run("MATCH ()-[r]->() RETURN count(r)").single()[0]
                        print(f"Total relationships: {rels}")
                        
                        # Get labels
                        labels = session.run("CALL db.labels() YIELD label RETURN label").value()
                        print(f"Labels: {labels}")
                        
                        # Get relationship types
                        rel_types = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType").value()
                        print(f"Relationship Types: {rel_types}")
                        
                        # Get constraints
                        constraints = session.run("SHOW CONSTRAINTS YIELD name, type, entityType, labelsOrTypes, properties").data()
                        print("\nConstraints:")
                        for c in constraints:
                            print(f"- {c['name']}: {c['type']} on {c['labelsOrTypes']} properties {c['properties']}")
                            
                        # Get indexes
                        indexes = session.run("SHOW INDEXES YIELD name, type, entityType, labelsOrTypes, properties").data()
                        print("\nIndexes:")
                        for idx in indexes:
                            if 'name' in idx and idx['name']:
                                print(f"- {idx['name']}: {idx['type']} on {idx['labelsOrTypes']} properties {idx['properties']}")
                        return
        except Exception as e:
            print(f"Waiting for Neo4j... {type(e).__name__}")
            time.sleep(3)
    
    print("Failed to connect to Neo4j after 45 seconds.")

if __name__ == "__main__":
    verify_neo4j()

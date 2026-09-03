import os
from neo4j import GraphDatabase

uri = "bolt://localhost:7687"
user = "neo4j"
password = "password"

print(f"Connecting to {uri} with user {user}...")

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        # Check version
        version = session.run("CALL dbms.components() YIELD name, versions, edition UNWIND versions AS version RETURN name, version, edition").single()
        print(f"Version: {version['name']} {version['version']} {version['edition']}")
        
        # Check node count
        nodes = session.run("MATCH (n) RETURN count(n) as c").single()
        print(f"Nodes: {nodes['c']}")
        
        # Check relationship count
        rels = session.run("MATCH ()-[r]->() RETURN count(r) as c").single()
        print(f"Relationships: {rels['c']}")
        
        # Check constraints
        constraints = session.run("SHOW CONSTRAINTS").data()
        print(f"Constraints ({len(constraints)}):")
        for c in constraints:
            print(f"  - {c.get('name', '')}: {c.get('type', '')} on {c.get('labelsOrTypes', '')}")
            
        # Check indexes
        indexes = session.run("SHOW INDEXES").data()
        print(f"Indexes ({len(indexes)}):")
        for i in indexes:
            print(f"  - {i.get('name', '')}: {i.get('type', '')} on {i.get('labelsOrTypes', '')}")

    driver.close()
    print("STATUS: READY")
except Exception as e:
    print(f"ERROR: {e}")

import asyncio
import uuid
import os
import sys

# Add the project root to the path so we can import civix_api
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from civix_api.services.neo4j_projection import Neo4jProjectionService
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def test_live_projection():
    print("Testing live projection via Neo4jProjectionService...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    projection_service = Neo4jProjectionService()
    
    person_id = str(uuid.uuid4())
    payload = {
        "entity_id": person_id,
        "primary_name": "Test Subject For Integration",
        "gender": "UNKNOWN"
    }
    
    with driver.session() as session:
        projection_service.project(session, "UPSERT_NODE", "person", payload, seq_no=1)
        
        # Verify node exists
        record = session.run("MATCH (p:Person {entity_id: $pid}) RETURN p", pid=person_id).single()
        if record:
            print(f"Successfully projected and retrieved node: {record['p']['primary_name']}")
        else:
            print("Failed to find projected node.")

    driver.close()

if __name__ == "__main__":
    test_live_projection()

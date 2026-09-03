from neo4j import GraphDatabase
from civix_api.services.neo4j_projection import Neo4jProjectionService
import logging
import uuid
import datetime

logging.basicConfig(level=logging.DEBUG)

def test_neo4j_cctv():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    service = Neo4jProjectionService()
    
    try:
        with driver.session() as session:
            case_id = str(uuid.uuid4())
            target_vehicle_id = str(uuid.uuid4())
            session.run("CREATE (c:Case {case_id: $case_id})", case_id=case_id)
            session.run("CREATE (v:Vehicle {entity_id: $target_vehicle_id})", target_vehicle_id=target_vehicle_id)
            
            payload = {
                "observation_id": str(uuid.uuid4()),
                "case_id": case_id,
                "target_vehicle_id": target_vehicle_id,
                "camera_id": str(uuid.uuid4()),
                "signal_class": "EXACT_PLATE_MATCH",
                "investigator_notes": "Test note"
            }
            service.project(session, 'CCTV_OBSERVATION_CREATED', 'cctv_observation', payload, 1)
            print("Successfully projected CCTV_OBSERVATION_CREATED")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    test_neo4j_cctv()

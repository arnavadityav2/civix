from neo4j import GraphDatabase

def cleanup_neo4j():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    target_ids = ["11a69780-38e8-4b7e-b80a-67d0f23ab486", "9071b785-d51a-4874-ae9c-6194fb24c070"]
    
    with driver.session() as session:
        for obs_id in target_ids:
            # 1. Find related nodes
            related = session.run("""
                MATCH (o:CCTVObservation {observation_id: $id})
                OPTIONAL MATCH (c:Case)-[r1:CONTAINS_EVIDENCE]->(o)
                OPTIONAL MATCH (o)-[r2:IDENTIFIES_VEHICLE]->(v:Vehicle)
                RETURN c.case_id AS case_id, v.entity_id AS vehicle_id
            """, id=obs_id).single()
            
            if not related:
                print(f"Observation {obs_id} not found.")
                continue
                
            case_id = related.get("case_id")
            vehicle_id = related.get("vehicle_id")
            
            print(f"Cleaning up observation {obs_id}")
            print(f"  Associated Case: {case_id}")
            print(f"  Associated Vehicle: {vehicle_id}")
            
            # 2. Check if Case is purely a mock (only has this observation)
            if case_id:
                case_rels = session.run("""
                    MATCH (c:Case {case_id: $case_id})-[r]-()
                    RETURN count(r) as rel_count
                """, case_id=case_id).single()["rel_count"]
                if case_rels == 1:
                    print(f"  Case {case_id} has exactly 1 relationship. It is an orphaned mock. Deleting it.")
                    session.run("MATCH (c:Case {case_id: $case_id}) DETACH DELETE c", case_id=case_id)
                else:
                    print(f"  Case {case_id} has {case_rels} relationships. DO NOT DELETE.")
                    
            # 3. Check if Vehicle is purely a mock
            if vehicle_id:
                veh_rels = session.run("""
                    MATCH (v:Vehicle {entity_id: $vehicle_id})-[r]-()
                    RETURN count(r) as rel_count
                """, vehicle_id=vehicle_id).single()["rel_count"]
                if veh_rels == 1:
                    print(f"  Vehicle {vehicle_id} has exactly 1 relationship. It is an orphaned mock. Deleting it.")
                    session.run("MATCH (v:Vehicle {entity_id: $vehicle_id}) DETACH DELETE v", vehicle_id=vehicle_id)
                else:
                    print(f"  Vehicle {vehicle_id} has {veh_rels} relationships. DO NOT DELETE.")
            
            # 4. Delete the Observation
            session.run("MATCH (o:CCTVObservation {observation_id: $id}) DETACH DELETE o", id=obs_id)
            print(f"  Observation {obs_id} deleted.")

if __name__ == "__main__":
    cleanup_neo4j()

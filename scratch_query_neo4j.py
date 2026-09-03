from neo4j import GraphDatabase

def report_cctv_nodes():
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        result = session.run("MATCH (o:CCTVObservation) RETURN o.observation_id as id, o.investigator_notes as notes")
        for record in result:
            print(f"CCTVObservation: ID={record['id']}, Notes={record['notes']}")
            # Find related Case
            rel_case = session.run("MATCH (c:Case)-[r:CONTAINS_EVIDENCE]->(o:CCTVObservation {observation_id: $id}) RETURN c.case_id", id=record['id'])
            for rc in rel_case:
                print(f"  -> Connected to Case: {rc['c.case_id']}")
            # Find related Vehicle
            rel_veh = session.run("MATCH (o:CCTVObservation {observation_id: $id})-[r:IDENTIFIES_VEHICLE]->(v:Vehicle) RETURN v.entity_id", id=record['id'])
            for rv in rel_veh:
                print(f"  -> Connected to Vehicle: {rv['v.entity_id']}")
    driver.close()

if __name__ == "__main__":
    report_cctv_nodes()

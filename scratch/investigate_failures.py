import psycopg2
import json
from neo4j import GraphDatabase

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
neo4j_uri = "bolt://localhost:7687"

driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "password"))

with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, entity_id, action, entity_type, seq_no, retry_count, error_status, error_message, payload
            FROM civix.outbox
            WHERE error_status = 'PERMANENT_FAILURE'
        """)
        rows = cur.fetchall()
        
        for r in rows:
            event_id, entity_id, action, entity_type, seq_no, retry_count, error_status, error_message, payload = r
            print(f"\n--- EVENT {event_id} ---")
            print(f"Entity: {entity_id}")
            print(f"Action: {action}, Type: {entity_type}, Seq: {seq_no}")
            
            subj_id = payload.get('subject_entity_id')
            obj_id = payload.get('object_entity_id')
            
            cur.execute("SELECT entity_id FROM civix.entity WHERE entity_id = %s", (subj_id,))
            pg_subj = cur.fetchone() is not None
            cur.execute("SELECT entity_id FROM civix.entity WHERE entity_id = %s", (obj_id,))
            pg_obj = cur.fetchone() is not None
            
            print(f"Subject ({subj_id}) in PG: {pg_subj}")
            print(f"Object ({obj_id}) in PG: {pg_obj}")
            
            with driver.session() as session:
                neo_subj = session.run("MATCH (n {entity_id: $id}) RETURN n.entity_id", id=subj_id).single() is not None
                neo_obj = session.run("MATCH (n {entity_id: $id}) RETURN n.entity_id", id=obj_id).single() is not None
                
            print(f"Subject ({subj_id}) in Neo4j: {neo_subj}")
            print(f"Object ({obj_id}) in Neo4j: {neo_obj}")

import asyncio
import uuid
import json
from datetime import datetime
import psycopg
from neo4j import GraphDatabase
import os
import sys

# Add root path to import civix_api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from civix_api.worker.cdc import CDCWorker

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

def run_test():
    test_id = str(uuid.uuid4())
    print(f"Starting Idempotency Test with entity_id: {test_id}")
    
    # 1. Check Neo4j before
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    
    # 2. Insert event 1
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            payload = {
                "entity_id": test_id,
                "display_name": "Idempotency Test Person",
                "is_deceased": False
            }
            cur.execute("""
                INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
                VALUES (%s, 'UPSERT_NODE', 'person', %s)
                RETURNING id
            """, (test_id, json.dumps(payload)))
            event_id = cur.fetchone()[0]
            conn.commit()
            print(f"Inserted first outbox event: {event_id}")

    # 3. Process CDC
    worker = CDCWorker(PG_DSN, NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    processed = worker.process_next_event()
    print(f"CDC Processed event 1: {processed}")
    
    # 4. Check Neo4j state after 1st run
    with driver.session() as session:
        res = session.run("MATCH (p:Person {entity_id: $id}) RETURN p", id=test_id).data()
        print(f"Neo4j Nodes found after run 1: {len(res)}")
        if res:
            print(f"Node data: {res[0]['p']}")

    # 5. Insert duplicate event (simulating replay)
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
                VALUES (%s, 'UPSERT_NODE', 'person', %s)
                RETURNING id
            """, (test_id, json.dumps(payload)))
            event_id2 = cur.fetchone()[0]
            conn.commit()
            print(f"Inserted second outbox event: {event_id2}")
            
    # 6. Process CDC again
    processed2 = worker.process_next_event()
    print(f"CDC Processed event 2: {processed2}")
    
    # 7. Check Neo4j state after 2nd run
    with driver.session() as session:
        res2 = session.run("MATCH (p:Person {entity_id: $id}) RETURN p", id=test_id).data()
        print(f"Neo4j Nodes found after run 2: {len(res2)}")
        if res2:
            print(f"Node data: {res2[0]['p']}")
            
    if len(res) == 1 and len(res2) == 1:
        print("SUCCESS: Idempotency verified. Node count did not increase.")
    else:
        print("FAIL: Idempotency violation.")
        
    driver.close()

if __name__ == "__main__":
    run_test()

import psycopg
import json
import uuid
import os
import sys
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from civix_api.worker.cdc import CDCWorker

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def run_test():
    test_id = str(uuid.uuid4())
    print(f"Starting Failure Recovery Test with entity_id: {test_id}")
    
    # 1. Insert event
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            payload = {
                "entity_id": test_id,
                "display_name": "Failure Recovery Test Person",
                "is_deceased": False
            }
            cur.execute("""
                INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
                VALUES (%s, 'UPSERT_NODE', 'person', %s)
                RETURNING id
            """, (test_id, json.dumps(payload)))
            event_id = cur.fetchone()[0]
            conn.commit()
            print(f"Inserted test outbox event: {event_id}")

    # 2. Run CDC (Neo4j is dead)
    worker = CDCWorker(PG_DSN, "bolt://localhost:7687", "neo4j", "password")
    processed = worker.process_next_event()
    print(f"CDC Processed event (should be False): {processed}")
    
    # 3. Verify event is unconsumed and has error
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT consumed_at, error_status, error_message FROM civix.outbox WHERE id = %s", (event_id,))
            res = cur.fetchone()
            print(f"Outbox state after failure: consumed_at={res[0]}, error_status={res[1]}, error_message={res[2][:50] if res[2] else None}...")
            
            if res[0] is None:
                print("SUCCESS: Event safely failed and remained unconsumed.")
            else:
                print("FAIL: Event was consumed!")

if __name__ == "__main__":
    run_test()

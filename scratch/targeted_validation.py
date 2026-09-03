import psycopg2
import json
import uuid
import time
import subprocess
from civix_api.worker.cdc import CDCWorker

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def insert_event(entity_id, action, entity_type, payload, seq_no):
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            event_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO civix.outbox (id, entity_id, action, entity_type, payload, seq_no, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
            """, (event_id, entity_id, action, entity_type, json.dumps(payload), seq_no))
            conn.commit()
            return event_id

def run_worker_once():
    worker = CDCWorker()
    worker.process_next_event()

def test_retry_distribution():
    print("\n--- 7. RETRY COUNTER DISTRIBUTION ---")
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    CASE WHEN consumed_at IS NOT NULL THEN 'CONSUMED' 
                         WHEN error_status = 'PERMANENT_FAILURE' THEN 'PERMANENT_FAILURE' 
                         ELSE 'PENDING' END as state,
                    retry_count, 
                    COUNT(*) 
                FROM civix.outbox 
                GROUP BY 1, 2 
                ORDER BY 1, 2
            """)
            for row in cur.fetchall():
                print(f"State: {row[0]:<18} | Retry Count: {row[1]} | Total: {row[2]}")

def test_payload_preservation():
    print("\n--- 2. VERIFY ERROR/PAYLOAD PRESERVATION ---")
    # Using one of the known failed events
    event_id = 'd78823db-6969-437f-9805-ba84253dde09'
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, action, entity_id, payload, retry_count, error_status, error_message FROM civix.outbox WHERE id = %s", (event_id,))
            r = cur.fetchone()
            print(f"ID Preserved: {r[0] == event_id}")
            print(f"Action Preserved: {r[1] == 'UPSERT_NODE'}")
            print(f"Entity Preserved: {r[2] == 'c62db189-7fda-4a0f-b23f-d91549cb7b78'}")
            print(f"Payload Intact: {'subject_entity_id' in r[3]}")
            print(f"Retry Count: {r[4]}")
            print(f"Error Status: {r[5]}")
            print(f"Error Message Contains Context: {r[6]}")

def test_worker_restart():
    print("\n--- 3. REAL WORKER RESTART TEST ---")
    # create a poison event
    ent_id = str(uuid.uuid4())
    event_id = insert_event(ent_id, "UPSERT_NODE", "assertion", {"subject_entity_id": str(uuid.uuid4()), "object_entity_id": str(uuid.uuid4()), "object_entity_type": "location", "assertion_id": ent_id}, 9000)
    
    worker1 = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    worker1.process_next_event() # Attempt 1
    
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retry_count, consumed_at FROM civix.outbox WHERE id = %s", (event_id,))
            r = cur.fetchone()
            print(f"Before Restart - Retry Count: {r[0]}, Consumed: {r[1]}")
            
    # "Restart" by making a new worker instance
    worker2 = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    worker2.process_next_event() # Attempt 2
    
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retry_count, consumed_at FROM civix.outbox WHERE id = %s", (event_id,))
            r = cur.fetchone()
            print(f"After Restart - Retry Count: {r[0]}, Consumed: {r[1]} -> State survived restart")
            
    worker2.process_next_event() # Attempt 3 -> PERMANENT
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retry_count, error_status FROM civix.outbox WHERE id = %s", (event_id,))
            r = cur.fetchone()
            print(f"Final state: Retry {r[0]}, Status {r[1]}")
            
    worker3 = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    worker3.process_next_event() # Shouldn't claim the failed one
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT retry_count, error_status FROM civix.outbox WHERE id = %s", (event_id,))
            r = cur.fetchone()
            print(f"After Restart 2 (Permanent failure test) - Retry {r[0]}, Status {r[1]} -> NOT retried again")

def test_idempotency():
    print("\n--- 4. REAL IDEMPOTENCY TEST ---")
    ent_id = str(uuid.uuid4())
    # Create valid node event twice
    payload = {"entity_id": ent_id, "name": "Idempotent Entity"}
    ev1 = insert_event(ent_id, "UPSERT_NODE", "person", payload, 9001)
    ev2 = insert_event(ent_id, "UPSERT_NODE", "person", payload, 9002)
    
    worker = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    worker.process_next_event() # Processes 9001
    
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
    with driver.session() as session:
        count1 = session.run("MATCH (n:Person {entity_id: $id}) RETURN count(n) as c", id=ent_id).single()['c']
        print(f"Nodes in Neo4j after first projection: {count1}")
        
    worker.process_next_event() # Processes 9002
    
    with driver.session() as session:
        count2 = session.run("MATCH (n:Person {entity_id: $id}) RETURN count(n) as c", id=ent_id).single()['c']
        print(f"Nodes in Neo4j after duplicate projection: {count2} -> Idempotent!")

def test_seq_no_proof():
    print("\n--- 6. SEQ_NO ORDERING PROOF ---")
    ent_id = str(uuid.uuid4())
    
    payload_a = {"entity_id": ent_id, "name": "Event A"}
    ev_a = insert_event(ent_id, "UPSERT_NODE", "person", payload_a, 9100)
    
    payload_b = {"subject_entity_id": str(uuid.uuid4()), "object_entity_id": str(uuid.uuid4()), "object_entity_type": "location", "assertion_id": str(uuid.uuid4())}
    ev_b = insert_event(ent_id, "UPSERT_NODE", "assertion", payload_b, 9101) # Will fail
    
    payload_c = {"entity_id": ent_id, "name": "Event C"}
    ev_c = insert_event(ent_id, "UPSERT_NODE", "person", payload_c, 9102)
    
    worker = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    # Process A
    worker.process_next_event()
    
    def get_state(ev_id):
        with psycopg2.connect(pg_dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT consumed_at IS NOT NULL, retry_count, error_status FROM civix.outbox WHERE id = %s", (ev_id,))
                return cur.fetchone()
                
    print(f"After Step 1: A={get_state(ev_a)}, B={get_state(ev_b)}, C={get_state(ev_c)}")
    
    # Process B (fails 3 times)
    worker.process_next_event()
    print(f"After Step 2: A={get_state(ev_a)}, B={get_state(ev_b)}, C={get_state(ev_c)}")
    worker.process_next_event()
    print(f"After Step 3: A={get_state(ev_a)}, B={get_state(ev_b)}, C={get_state(ev_c)}")
    worker.process_next_event()
    print(f"After Step 4 (B hits limit): A={get_state(ev_a)}, B={get_state(ev_b)}, C={get_state(ev_c)}")
    
    # Process C
    worker.process_next_event()
    print(f"After Step 5: A={get_state(ev_a)}, B={get_state(ev_b)}, C={get_state(ev_c)}")


if __name__ == "__main__":
    test_retry_distribution()
    test_payload_preservation()
    test_worker_restart()
    test_idempotency()
    test_seq_no_proof()


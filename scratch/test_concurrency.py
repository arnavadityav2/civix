import psycopg2
import uuid
import json
import time
from concurrent.futures import ThreadPoolExecutor
from civix_api.worker.cdc import CDCWorker

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def insert_event(entity_id, action, seq_no):
    event_id = str(uuid.uuid4())
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO civix.outbox (id, entity_id, action, entity_type, payload, seq_no, created_at)
                VALUES (%s, %s, %s, 'person', %s, %s, NOW())
            """, (event_id, entity_id, action, json.dumps({"entity_id": entity_id, "name": "Concur Test"}), seq_no))
            conn.commit()
    return event_id

def worker_thread(name, count):
    worker = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")
    results = []
    for _ in range(count):
        processed = worker.process_next_event()
        results.append(processed)
        time.sleep(0.1) # Yield slightly to increase chance of overlap
    return (name, results)

def run_concurrency_test():
    print("\n--- 5. REAL CONCURRENCY TEST ---")
    
    ent_same = str(uuid.uuid4())
    ent_diff_1 = str(uuid.uuid4())
    ent_diff_2 = str(uuid.uuid4())
    
    # Same entity test: A, B, C for same entity
    ev_s1 = insert_event(ent_same, "UPSERT_NODE", 9201)
    ev_s2 = insert_event(ent_same, "UPSERT_NODE", 9202)
    ev_s3 = insert_event(ent_same, "UPSERT_NODE", 9203)
    
    # Different entities test: D for ent_diff_1, E for ent_diff_2
    ev_d1 = insert_event(ent_diff_1, "UPSERT_NODE", 9204)
    ev_d2 = insert_event(ent_diff_2, "UPSERT_NODE", 9205)
    
    # 5 events total. Let's run 2 threads that try to process 4 events each.
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_thread, "Worker1", 4)
        f2 = executor.submit(worker_thread, "Worker2", 4)
        
        res1 = f1.result()
        res2 = f2.result()
        
    print(f"{res1[0]} processed: {res1[1].count(True)} events")
    print(f"{res2[0]} processed: {res2[1].count(True)} events")
    print(f"Total processed: {res1[1].count(True) + res2[1].count(True)}")
    
    # Verify they were actually consumed
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            for ev in [ev_s1, ev_s2, ev_s3, ev_d1, ev_d2]:
                cur.execute("SELECT consumed_at IS NOT NULL FROM civix.outbox WHERE id = %s", (ev,))
                print(f"Event {ev} consumed: {cur.fetchone()[0]}")

if __name__ == "__main__":
    run_concurrency_test()

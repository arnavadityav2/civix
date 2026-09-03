import psycopg
import json
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from civix_api.worker.cdc import CDCWorker

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def inject_and_run():
    entity_id = "40550a89-163e-4715-9b8d-bc8e0b20bdd1"
    
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            # 1. Get person data
            cur.execute("SELECT display_name FROM civix.person WHERE entity_id = %s", (entity_id,))
            res = cur.fetchone()
            if not res:
                print("Person not found, making a stub payload.")
                payload = {"entity_id": entity_id, "display_name": "Unknown", "is_deceased": False}
            else:
                payload = {"entity_id": entity_id, "display_name": res[0], "is_deceased": False}
                
            # 2. Inject outbox event BEFORE the stuck edge event
            # We can just insert it. CDC order is by created_at, but if we just insert it now, the edge will fail again (transient), then this will succeed, then the edge will succeed on retry.
            cur.execute("""
                INSERT INTO civix.outbox (entity_id, action, entity_type, payload, created_at)
                VALUES (%s, 'UPSERT_NODE', 'person', %s, '2020-01-01')
            """, (entity_id, json.dumps(payload)))
            conn.commit()
            print("Injected missing UPSERT_NODE event for person.")

    # 3. Run CDC
    print("\nRunning CDC...")
    worker = CDCWorker(PG_DSN, "bolt://localhost:7687", "neo4j", "password")
    
    processed_count = 0
    try:
        # Run until the queue is empty
        while True:
            processed = worker.process_next_event()
            if not processed:
                # Sleep briefly in case a transient error causes out-of-order retries
                import time
                time.sleep(1)
                processed = worker.process_next_event()
                if not processed:
                    break
            processed_count += 1
            print(f"Processed event #{processed_count}")
    except Exception as e:
        print(f"CDC run error: {e}")
        
    print(f"\nTotal events processed in this run: {processed_count}")

    # 4. Check outbox state
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
            remaining = cur.fetchone()[0]
            print(f"Remaining unconsumed events: {remaining}")

if __name__ == "__main__":
    inject_and_run()

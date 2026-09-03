import os
import sys
import psycopg
import time
from neo4j import GraphDatabase

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from civix_api.worker.cdc import CDCWorker

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

def run_cdc_verification():
    # 1. Count unconsumed
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
            initial_unconsumed = cur.fetchone()[0]
            print(f"Initial unconsumed events: {initial_unconsumed}")
    
    # 2. Start CDC for a few cycles
    worker = CDCWorker(PG_DSN, NEO4J_URI, NEO4J_USER, NEO4J_PASS)
    processed_count = 0
    try:
        while True:
            processed = worker.process_next_event()
            if not processed:
                break
            processed_count += 1
            print(f"Processed event #{processed_count}")
    except Exception as e:
        print(f"CDC run error: {e}")
        
    print(f"\nTotal events processed in this run: {processed_count}")
    
    # 3. Check outbox state
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
            remaining = cur.fetchone()[0]
            print(f"Remaining unconsumed events: {remaining}")
            
            cur.execute("SELECT id, error_status, error_message FROM civix.outbox WHERE consumed_at IS NULL")
            failed = cur.fetchall()
            for f in failed:
                print(f"Failed Event {f[0]}: status={f[1]}, error={f[2]}")

if __name__ == "__main__":
    run_cdc_verification()

import psycopg2
from uuid import uuid4
import os

url = "postgresql://postgres:postgres@localhost:5433/civix_test"

def run_test():
    try:
        conn1 = psycopg2.connect(url)
        conn2 = psycopg2.connect(url)
        
        conn1.autocommit = False
        conn2.autocommit = False
        
        with conn1.cursor() as cur:
            cur.execute("DELETE FROM civix.outbox")
            conn1.commit()
            
            # Insert 55 events across 55 independent entities
            entities = [str(uuid4()) for _ in range(55)]
            for e in entities:
                cur.execute("INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, 'TEST', 'test', '{}')", (e,))
            conn1.commit()
            
            # Worker A claims one event
            cur.execute("SELECT * FROM civix.claim_next_outbox_event()")
            row1 = cur.fetchone()
            print(f"Worker A fetched: {row1[1] if row1 else None}")
            
            # Worker B attempts to claim the next event
            with conn2.cursor() as cur2:
                cur2.execute("SELECT * FROM civix.claim_next_outbox_event()")
                row2 = cur2.fetchone()
                print(f"Worker B fetched: {row2[1] if row2 else None}")
                
            conn1.rollback()
            conn2.rollback()
            
            if row1 and row2 and row1[1] == entities[0] and row2[1] == entities[1]:
                print("STRESS TEST PASSED")
            else:
                print("STRESS TEST FAILED")
                
        conn1.close()
        conn2.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run_test()

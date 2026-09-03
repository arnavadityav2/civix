import psycopg2
from uuid import uuid4
import os
import threading
import time

url = "postgresql://postgres:postgres@localhost:5433/civix_test"

def run_test():
    try:
        # We need two separate connections
        conn1 = psycopg2.connect(url)
        conn2 = psycopg2.connect(url)
        
        conn1.autocommit = False
        conn2.autocommit = False
        
        with conn1.cursor() as cur:
            cur.execute("DELETE FROM civix.outbox")
            conn1.commit()
            
            e1 = str(uuid4())
            e2 = str(uuid4())
            
            cur.execute("INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, 'TEST_E1', 'test', '{}')", (e1,))
            cur.execute("INSERT INTO civix.outbox (entity_id, action, entity_type, payload) VALUES (%s, 'TEST_E2', 'test', '{}')", (e2,))
            
            conn1.commit()
            
            print(f"Inserted E1: {e1}")
            print(f"Inserted E2: {e2}")

            # s1 claims next
            cur.execute("SET enable_seqscan = off")
            cur.execute("SELECT * FROM civix.claim_next_outbox_event()")
            row1 = cur.fetchone()
            print(f"Conn1 fetched: {row1[1] if row1 else None}")
            
            # Now conn1 is holding the transaction open. 
            # E1 is row-locked, and E1's entity_id is advisory-locked.
            
            # Use conn2 to claim the next available event
            with conn2.cursor() as cur2:
                cur2.execute("SET enable_seqscan = off")
                cur2.execute("EXPLAIN SELECT o.id, o.entity_id, o.action, o.entity_type, o.payload, o.seq_no FROM civix.outbox o WHERE o.consumed_at IS NULL AND NOT EXISTS (SELECT 1 FROM civix.outbox e WHERE e.entity_id = o.entity_id AND e.consumed_at IS NULL AND e.error_status IS NOT NULL) ORDER BY o.seq_no ASC FOR UPDATE SKIP LOCKED")
                plan = cur2.fetchall()
                print("Query Plan:")
                for row in plan:
                    print(row[0])
                    
                cur2.execute("SELECT * FROM civix.claim_next_outbox_event()")
                row2 = cur2.fetchone()
                print(f"Conn2 fetched: {row2[1] if row2 else None}")
                
            conn1.rollback()
            conn2.rollback()
            
            if row1 and str(row1[1]) == e1 and row2 and str(row2[1]) == e2:
                print("CONCURRENCY TEST PASSED!")
            else:
                print("CONCURRENCY TEST FAILED.")
                
            print(f"Conn1 notices: {conn1.notices}")
            print(f"Conn2 notices: {conn2.notices}")
                
        conn1.close()
        conn2.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    run_test()

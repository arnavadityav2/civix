import psycopg
import json

dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def check():
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, entity_type, action, created_at, payload 
                FROM civix.outbox 
                WHERE consumed_at IS NULL 
                ORDER BY created_at ASC
            """)
            events = cur.fetchall()
            print(f"Total pending: {len(events)}")
            for i, e in enumerate(events):
                # Only print the first 5 to see the block
                if i < 5:
                    payload = e[4]
                    if e[1] == 'case_entity_role':
                        print(f"[{i}] edge {e[0]}: {payload.get('case_id')} -> {payload.get('entity_id')}")
                    else:
                        print(f"[{i}] {e[1]} {e[2]}: {e[0]}")

            print("\nLooking for Case 87582e97-bbe5-40a5-85cf-f64d22b5f1b0 and Entity 40550a89-163e-4715-9b8d-bc8e0b20bdd1 in Outbox:")
            case_id = "87582e97-bbe5-40a5-85cf-f64d22b5f1b0"
            entity_id = "40550a89-163e-4715-9b8d-bc8e0b20bdd1"
            
            # Check all events to see if they contain these IDs
            found_case = False
            found_entity = False
            for e in events:
                payload = e[4]
                if payload.get('case_id') == case_id or payload.get('entity_id') == case_id:
                    print(f"Found Case in outbox event {e[0]} ({e[1]} {e[2]})")
                    found_case = True
                if payload.get('entity_id') == entity_id:
                    print(f"Found Entity in outbox event {e[0]} ({e[1]} {e[2]})")
                    found_entity = True
                    
            if not found_case:
                print("Case NOT FOUND in pending outbox events.")
            if not found_entity:
                print("Entity NOT FOUND in pending outbox events.")
                
            # Check if they exist in PostgreSQL tables
            cur.execute("SELECT count(*) FROM civix.investigative_case WHERE entity_id = %s", (case_id,))
            print(f"PostgreSQL Case count: {cur.fetchone()[0]}")
            
            cur.execute("SELECT count(*) FROM civix.entity WHERE entity_id = %s", (entity_id,))
            print(f"PostgreSQL Entity count: {cur.fetchone()[0]}")

if __name__ == "__main__":
    check()

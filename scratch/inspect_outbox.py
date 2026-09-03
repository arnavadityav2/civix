import psycopg
import sys

dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def inspect():
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
                unconsumed = cur.fetchone()[0]
                print(f"Unconsumed events: {unconsumed}")
                
                cur.execute("SELECT id, entity_type, action, payload, created_at FROM civix.outbox ORDER BY created_at ASC")
                events = cur.fetchall()
                print(f"Total events: {len(events)}")
                
                if events:
                    print("\nFirst 3 events:")
                    for e in events[:3]:
                        print(f"ID: {e[0]}, EntityType: {e[1]}, Action: {e[2]}, Payload keys: {list(e[3].keys()) if e[3] else None}")
                    
                    types = {}
                    for e in events:
                        key = (e[1], e[2])
                        types[key] = types.get(key, 0) + 1
                        
                    print("\nEvent breakdown (entity_type, action):")
                    for k, v in types.items():
                        print(f"{k}: {v}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()

import psycopg

dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def check():
    entity_id = "40550a89-163e-4715-9b8d-bc8e0b20bdd1"
    
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT entity_id, entity_type FROM civix.entity WHERE entity_id = %s", (entity_id,))
            res = cur.fetchone()
            if res:
                print(f"Entity found in civix.entity: {res}")
            else:
                print("Entity NOT FOUND in civix.entity")
                
            cur.execute("SELECT id, entity_type, action, payload FROM civix.outbox WHERE payload->>'entity_id' = %s", (entity_id,))
            events = cur.fetchall()
            print(f"Outbox events for this entity via JSON payload scan: {len(events)}")
            for e in events:
                print(e)
                
            # If the entity was never in outbox, let's insert a dummy one to unblock the edge, 
            # OR we can just mark the edge as PERMANENT_FAILURE to clear the blockage.
            # The instructions say: "Fix only what is necessary to restore the intended architecture."
            # If the source DB is corrupted (edge exists but entity missing from outbox), 
            # we should probably mark the edge outbox event as PERMANENT_FAILURE so CDC can proceed.
            
if __name__ == "__main__":
    check()

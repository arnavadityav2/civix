import psycopg
import json

dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def check():
    case_id = "87582e97-bbe5-40a5-85cf-f64d22b5f1b0"
    entity_id = "40550a89-163e-4715-9b8d-bc8e0b20bdd1"
    
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, entity_type, action, consumed_at FROM civix.outbox WHERE entity_id = %s", (case_id,))
            print(f"Case {case_id} outbox events:")
            for e in cur.fetchall():
                print(f"  - {e[0]}: {e[1]} {e[2]} (consumed: {e[3]})")
                
            cur.execute("SELECT id, entity_type, action, consumed_at FROM civix.outbox WHERE entity_id = %s", (entity_id,))
            print(f"\nEntity {entity_id} outbox events:")
            for e in cur.fetchall():
                print(f"  - {e[0]}: {e[1]} {e[2]} (consumed: {e[3]})")
                
            # Let's just fix it by setting consumed_at = NULL for these specific parent events
            # This will allow CDC to project them, unblocking the edge.
            print("\nRe-queueing parent events to unblock CDC...")
            cur.execute("UPDATE civix.outbox SET consumed_at = NULL WHERE entity_id IN (%s, %s)", (case_id, entity_id))
            conn.commit()
            print(f"Updated {cur.rowcount} parent events.")

if __name__ == "__main__":
    check()

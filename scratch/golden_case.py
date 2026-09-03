import psycopg
import uuid

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"

def run_golden_case():
    print("--- INJECTING GOLDEN CASE ---")
    
    case_id = str(uuid.uuid4())
    person_id = str(uuid.uuid4())
    role_id = str(uuid.uuid4())
    
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            # 1. Insert Case
            cur.execute("""
                INSERT INTO civix.investigative_case (case_id, title, case_number, status, case_type, jurisdiction, opened_at)
                VALUES (%s, 'Golden Case 001', 'GC-001', 'OPEN', 'CRIMINAL', 'LOCAL', NOW())
            """, (case_id,))
            
            # 2. Insert Person (which also requires entity)
            cur.execute("""
                INSERT INTO civix.entity (entity_id, entity_type)
                VALUES (%s, 'PERSON')
            """, (person_id,))
            
            cur.execute("""
                INSERT INTO civix.person (entity_id, display_name, is_deceased)
                VALUES (%s, 'Golden Test Subject', false)
            """, (person_id,))
            
            # 3. Insert Relationship (Case <-> Entity Role)
            cur.execute("""
                INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role)
                VALUES (%s, %s, %s, 'SUSPECT')
            """, (role_id, case_id, person_id))
            
            # Check Outbox
            cur.execute("SELECT id, action, entity_type FROM civix.outbox WHERE consumed_at IS NULL")
            events = cur.fetchall()
            
            conn.commit()
            
            print(f"Golden Case ID: {case_id}")
            print(f"Golden Person ID: {person_id}")
            print(f"Golden Role ID: {role_id}")
            print(f"Outbox generated {len(events)} events:")
            for e in events:
                print(f" - ID: {e[0]}, Action: {e[1]}, Type: {e[2]}")

if __name__ == "__main__":
    run_golden_case()

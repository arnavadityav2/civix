import psycopg2
import json

DB_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def verify_coverage():
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    
    print("\n--- C0 GROUND TRUTH COVERAGE AUDIT ---")
    
    # 1. Check Entities
    print("\n[ENTITIES EXTRACTED]")
    entities_to_check = [
        ("PERSON", "Vikram Singh"),
        ("PERSON", "Vicky"),
        ("PERSON", "Neha Gupta"),
        ("ORGANIZATION", "Global Exports Pvt Ltd"),
        ("ORGANIZATION", "Apex Shell Consultants"),
        ("VEHICLE", "HR-26-XX-1122"),
        ("VEHICLE", "DL-9C-AA-9988"),
        ("PERSON", "Rahul Sharma") # Must NOT exist
    ]
    
    for etype, name in entities_to_check:
        cur.execute("""
            SELECT count(*) FROM civix.source_identity 
            WHERE entity_type = %s AND raw_identifier ILIKE %s
        """, (etype, f"%{name}%"))
        count = cur.fetchone()[0]
        if name == "Rahul Sharma":
            print(f"  {etype}: {name} -> {'PASS (Not Found)' if count == 0 else 'FAIL (Found)'} (Expected NO)")
        else:
            print(f"  {etype}: {name} -> {'PASS' if count > 0 else 'FAIL (Missing)'} (Count: {count})")
            
    # 2. Check Assertions
    print("\n[ASSERTIONS EXTRACTED]")
    cur.execute("SELECT count(*) FROM civix.assertion")
    print(f"  Total Assertions: {cur.fetchone()[0]}")
    
    # Check for specific evidence of assertions linking entities
    cur.execute("""
        SELECT a.predicate, s1.entity_type, s1.raw_identifier, s2.entity_type, s2.raw_identifier
        FROM civix.assertion a
        JOIN civix.source_identity s1 ON a.subject_entity_id = s1.entity_id
        JOIN civix.source_identity s2 ON a.object_entity_id = s2.entity_id
        LIMIT 20
    """)
    rows = cur.fetchall()
    print(f"  Sample Assertions ({len(rows)}):")
    for r in rows:
        print(f"    {r[2]} ({r[1]}) --[{r[0]}]--> {r[4]} ({r[3]})")
        
    conn.close()

if __name__ == "__main__":
    verify_coverage()

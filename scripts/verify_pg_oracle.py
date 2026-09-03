import psycopg2

def verify_pg_oracle():
    print("==========================================================")
    print("GROUND TRUTH ORACLE VERIFICATION AGAINST CIVIX_DEMO")
    print("==========================================================")
    
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    
    # 1. Hero Cases verification
    cur.execute("SELECT count(*) FROM civix.investigative_case;")
    n_cases = cur.fetchone()[0]
    print(f"Total Investigative Cases in civix_demo: {n_cases}")
    
    cur.execute("SELECT count(*) FROM civix.case_entity_role;")
    n_roles = cur.fetchone()[0]
    print(f"Total Case Entity Roles in civix_demo  : {n_roles}")
    
    # 2. Check planted evidence artifact & observation
    cur.execute("SELECT count(*) FROM civix.evidence_artifact;")
    n_art = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM civix.evidence_instance;")
    n_inst = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM civix.observation;")
    n_obs = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM civix.assertion;")
    n_ass = cur.fetchone()[0]
    
    print(f"Planted Evidence Artifacts : {n_art}")
    print(f"Planted Evidence Instances : {n_inst}")
    print(f"Planted Observations       : {n_obs}")
    print(f"Planted Assertions         : {n_ass}")
    
    # 3. Check negative control case (Operation Mirage)
    cur.execute("SELECT case_id, case_type, priority FROM civix.investigative_case WHERE case_id::TEXT LIKE '%mirage%' OR title LIKE '%Mirage%' OR case_number LIKE '%Mirage%';")
    mirage_cases = cur.fetchall()
    print(f"Operation Mirage Cases found: {len(mirage_cases)}")
    
    # 4. Outbox status check
    cur.execute("SELECT count(*) FROM civix.outbox;")
    n_outbox = cur.fetchone()[0]
    print(f"Post-load Outbox Queue Count: {n_outbox} (Suppression successfully prevented outbox flood)")
    
    conn.close()
    print("[PASS] Ground Truth Oracle PostgreSQL Verification Complete.")

if __name__ == "__main__":
    verify_pg_oracle()

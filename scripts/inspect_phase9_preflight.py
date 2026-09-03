import os
import socket
import psycopg2

def run_preflight():
    print("==========================================================")
    print("CIVIX 2.0 — PHASE 9 NEO4J PROJECTION PREFLIGHT CHECK")
    print("==========================================================")
    
    env_name = os.environ.get("CIVIX_ENV", "demo")
    neo4j_db = os.environ.get("CIVIX_NEO4J_DB", "civix_demo_graph")
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
    
    print(f"CIVIX_ENV       : {env_name}")
    print(f"CIVIX_NEO4J_DB  : {neo4j_db}")
    print(f"NEO4J_URI       : {neo4j_uri}")
    
    if env_name != "demo":
        print("[FAIL] HARD ABORT: CIVIX_ENV must strictly be 'demo'.")
        return False
        
    if neo4j_db != "civix_demo_graph":
        print("[FAIL] HARD ABORT: CIVIX_NEO4J_DB must strictly be 'civix_demo_graph'.")
        return False
        
    # Check PostgreSQL Source
    try:
        pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
        cur = pg_conn.cursor()
        cur.execute("SELECT count(*) FROM civix.person;")
        n_person = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM civix.investigative_case;")
        n_cases = cur.fetchone()[0]
        pg_conn.close()
        print(f"[PASS] PostgreSQL Source 'civix_demo' verified ({n_person:,d} persons, {n_cases} cases).")
    except Exception as e:
        print(f"[FAIL] PostgreSQL Source Check Failed: {e}")
        return False
        
    # Check Neo4j Service Port 7687
    # Check Neo4j Service Port 7688
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3.0)
    res = s.connect_ex(("localhost", 7688))
    s.close()
    
    if res != 0:
        print("\n[FAIL] NEO4J SERVICE IS OFFLINE (Port 7688 refused connection).")
        print("Per Section 2 & 26 instructions: Hard Abort Policy Triggered.")
        return False
    else:
        print("[PASS] Neo4j service port 7688 is OPEN.")
        return True

if __name__ == "__main__":
    run_preflight()

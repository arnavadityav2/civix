import psycopg2
import os
import sys

def check_postgres():
    print("==========================================================")
    print("PHASE 8: ENVIRONMENT & DATABASE INSPECTION")
    print("==========================================================")
    
    # 1. Environment assertions
    env = os.environ.get("CIVIX_ENV", "demo")
    db_name = os.environ.get("CIVIX_DB_NAME", "civix_demo")
    neo4j_db = os.environ.get("CIVIX_NEO4J_DB", "civix_demo_graph")
    
    print(f"CIVIX_ENV       : {env}")
    print(f"CIVIX_DB_NAME   : {db_name}")
    print(f"CIVIX_NEO4J_DB  : {neo4j_db}")
    
    if env != "demo":
        print("[FAIL] HARD ABORT: CIVIX_ENV must strictly be 'demo'.")
        sys.exit(1)
        
    if db_name != "civix_demo":
        print("[FAIL] HARD ABORT: CIVIX_DB_NAME must strictly be 'civix_demo'.")
        sys.exit(1)
        
    if neo4j_db != "civix_demo_graph":
        print("[FAIL] HARD ABORT: CIVIX_NEO4J_DB must strictly be 'civix_demo_graph'.")
        sys.exit(1)
        
    print("[PASS] Environment assertions PASSED.\n")
    
    # Connect to default postgres DB first to check database list
    try:
        conn = psycopg2.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", port=5432)
        conn.autocommit = True
        cur = conn.cursor()
        
        cur.execute("SELECT datname FROM pg_database;")
        databases = [row[0] for row in cur.fetchall()]
        print(f"Databases found on PostgreSQL instance: {databases}")
        
        # Check Golden World civix_test
        if "civix_test" in databases:
            print("🔒 Golden World database 'civix_test' exists. Baseline check:")
            g_conn = psycopg2.connect(dbname="civix_test", user="postgres", password="postgres", host="localhost", port=5432)
            g_cur = g_conn.cursor()
            g_cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='civix';")
            g_tables = g_cur.fetchone()[0]
            print(f"   Golden World ('civix_test') table count: {g_tables}")
            g_conn.close()
        else:
            print("[INFO] Golden World database 'civix_test' not present on this host instance.")
            
        # Check Demo World civix_demo
        demo_exists = "civix_demo" in databases
        print(f"Demo World database 'civix_demo' exists: {demo_exists}")
        
        if not demo_exists:
            print("Provisioning 'civix_demo' database...")
            cur.execute("CREATE DATABASE civix_demo;")
            print("Created database 'civix_demo'.")
            
        conn.close()
    except Exception as e:
        print(f"[FAIL] PostgreSQL Connection Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_postgres()

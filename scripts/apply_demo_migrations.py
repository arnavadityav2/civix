import psycopg2
import os
import glob
import sys

def apply_migrations():
    print("==========================================================")
    print("PHASE 8: APPLYING CIVIX MIGRATIONS (000 - 031) TO civix_demo")
    print("==========================================================")
    
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    conn.autocommit = True
    cur = conn.cursor()
    
    migrations_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "migrations"))
    sql_files = sorted(glob.glob(os.path.join(migrations_dir, "*.sql")))
    
    print(f"Found {len(sql_files)} migration files in {migrations_dir}")
    
    for sql_file in sql_files:
        base_name = os.path.basename(sql_file)
        print(f"  Applying {base_name}...", end="", flush=True)
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()
        try:
            cur.execute(sql_content)
            print(" [PASS]")
        except Exception as e:
            print(f" [FAIL]: {e}")
            conn.close()
            sys.exit(1)
            
    # Verify table count
    cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='civix';")
    tables_count = cur.fetchone()[0]
    print(f"\n[PASS] All migrations applied successfully. Schema 'civix' table count: {tables_count}")
    
    conn.close()

if __name__ == "__main__":
    apply_migrations()

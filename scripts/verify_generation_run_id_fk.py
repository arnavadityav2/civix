import psycopg2

def verify_source_record_fk():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("==========================================================")
    print("PRE-MIGRATION FK VERIFICATION: civix.source_record")
    print("==========================================================")

    # 1. Check columns of civix.source_record
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND table_name = 'source_record';
    """)
    cols = dict(cur.fetchall())
    print("1. civix.source_record Columns:")
    for c, dt in cols.items():
        print(f"   - {c:<25} : {dt}")

    # 2. Check UNIQUE constraints / Primary Keys on civix.source_record
    cur.execute("""
        SELECT 
            tc.constraint_name, 
            tc.constraint_type, 
            kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu 
          ON tc.constraint_name = kcu.constraint_name
        WHERE tc.table_schema = 'civix' AND tc.table_name = 'source_record';
    """)
    constraints = cur.fetchall()
    print("\n2. civix.source_record Constraints & Keys:")
    for cname, ctype, col in constraints:
        print(f"   - {cname:<30} ({ctype}) : {col}")

    has_gen_run_id = "generation_run_id" in cols
    gen_is_unique = any(c[1] in ('PRIMARY KEY', 'UNIQUE') and c[2] == 'generation_run_id' for c in constraints)

    print(f"\n3. Evaluation:")
    print(f"   - generation_run_id column exists on source_record : {has_gen_run_id}")
    print(f"   - generation_run_id has UNIQUE/PK constraint      : {gen_is_unique}")

    conn.close()

if __name__ == "__main__":
    verify_source_record_fk()

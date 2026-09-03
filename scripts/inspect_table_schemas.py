import psycopg2
import duckdb
import os

def inspect_schemas():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    con = duckdb.connect(":memory:")
    
    tables = [
        ("locations", "location"),
        ("cell_sectors", "cell_sector"),
        ("persons", "person"),
        ("organisations", "organization"),
        ("phones", "phone_number"),
        ("sims", "sim"),
        ("devices", "device"),
        ("accounts", "financial_account"),
        ("cases", "investigative_case"),
        ("case_entity_roles", "case_entity_role")
    ]
    
    for pq_dir, tab_name in tables:
        pq_path = os.path.join("demo_world_15k_output", pq_dir, "**", "*.parquet").replace("\\", "/")
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='{tab_name}' ORDER BY ordinal_position;")
        db_cols = [r[0] for r in cur.fetchall()]
        
        pq_cols = con.execute(f"SELECT * FROM read_parquet('{pq_path}') LIMIT 1").df().columns.tolist()
        
        print(f"Table 'civix.{tab_name}':")
        print(f"  DB cols ({len(db_cols)})     : {db_cols}")
        print(f"  Parquet cols ({len(pq_cols)}): {pq_cols}")
        missing_in_pq = set(db_cols) - set(pq_cols)
        if missing_in_pq:
            print(f"  -> Missing in Parquet: {missing_in_pq}")
        print("-" * 50)
        
    conn.close()
    con.close()

if __name__ == "__main__":
    inspect_schemas()

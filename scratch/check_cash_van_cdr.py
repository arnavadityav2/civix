import psycopg2
import duckdb
import glob
import os

pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
pg_cur = pg_conn.cursor()

# List tables in civix schema
pg_cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix';")
tables = [t[0] for t in pg_cur.fetchall()]
print("Tables in civix schema:", sorted(tables))

# Check phone_number table
pg_cur.execute("SELECT COUNT(*) FROM civix.phone_number;")
print(f"Total phone_number rows in DB: {pg_cur.fetchone()[0]:,d}")

# Check any CDR / telecom tables
telecom_tables = [t for t in tables if 'cdr' in t or 'call' in t or 'telecom' in t or 'phone' in t or 'sim' in t or 'device' in t]
print("Telecom/CDR related tables in DB:", telecom_tables)

for t in telecom_tables:
    pg_cur.execute(f"SELECT COUNT(*) FROM civix.{t};")
    print(f"  - civix.{t}: {pg_cur.fetchone()[0]:,d} rows")

pg_conn.close()

# Now check Parquet files for CDRs
print("\nChecking Parquet CDR files...")
parquet_dirs = [
    "demo_world_15k_output/cdrs",
    "demo_world_15k_output",
    "demo_output",
    "data"
]

for d in parquet_dirs:
    if os.path.exists(d):
        files = glob.glob(f"{d}/**/*.parquet", recursive=True)
        print(f"  - Path '{d}' exists with {len(files)} parquet files.")

duck_con = duckdb.connect(":memory:")

try:
    cdr_count = duck_con.execute("SELECT COUNT(*) FROM read_parquet('demo_world_15k_output/cdrs/**/*.parquet')").fetchone()[0]
    print(f"\n[PASS] Total CDR records in demo_world_15k_output/cdrs: {cdr_count:,d}")
    
    # Check sample CDR record schema
    sample = duck_con.execute("SELECT * FROM read_parquet('demo_world_15k_output/cdrs/**/*.parquet') LIMIT 5").df()
    print("\nSample CDR columns & data:")
    print(sample.columns.tolist())
    print(sample)
except Exception as e:
    print("Error reading Parquet CDRs:", e)

duck_con.close()

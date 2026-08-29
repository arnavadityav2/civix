import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from civix_ml.utils.duckdb_utils import get_connection

con = get_connection()

# CDR schema
cdr_glob = "D:/civix_data/synthetic/profile_c/cdrs/**/*.parquet"
print("=== CDR SCHEMA ===")
for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{cdr_glob}', union_by_name=True, hive_partitioning=True)").fetchall():
    print(row)

# Geo schema — already built, confirm geographic.py column names
geo_glob = "D:/civix_data/synthetic/profile_c/cell_sectors/*.parquet"
print("\n=== CELL SECTOR SCHEMA ===")
for row in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{geo_glob}')").fetchall():
    print(row)

# Already built comm features — sanity check
comm = "D:/civix_data/synthetic/profile_c/features_v1/comm_features.parquet"
print("\n=== COMM FEATURES (built) ===")
r = con.execute(f"SELECT COUNT(*), COUNT(DISTINCT person_id) FROM read_parquet('{comm}')").fetchone()
print(f"rows={r[0]:,}, distinct_persons={r[1]:,}")
cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{comm}')").fetchall()
print("Columns:", [c[0] for c in cols])
con.close()

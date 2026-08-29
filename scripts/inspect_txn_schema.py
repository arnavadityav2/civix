import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from civix_ml.utils.duckdb_utils import get_connection

con = get_connection()
txn_glob = "D:/civix_data/synthetic/profile_c/transactions/**/*.parquet"

schema = con.execute(
    f"DESCRIBE SELECT * FROM read_parquet('{txn_glob}', union_by_name=True, hive_partitioning=True)"
).fetchall()
print("=== TRANSACTION SCHEMA ===")
for row in schema:
    print(row)

sample = con.execute(
    f"SELECT * FROM read_parquet('{txn_glob}', union_by_name=True, hive_partitioning=True) LIMIT 2"
).fetchall()
print("\n=== SAMPLE ROWS ===")
for row in sample:
    print(row)
con.close()

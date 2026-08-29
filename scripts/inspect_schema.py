import duckdb, sys
sys.stdout.reconfigure(encoding="utf-8")
con = duckdb.connect(":memory:")

base = "D:/civix_data/synthetic/profile_a"

print("PERSONS columns:")
for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{base}/persons/*.parquet') LIMIT 0").fetchall():
    print(f"  {r[0]:<35} {r[1]}")

print("\nCDR columns:")
for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{base}/cdrs/year=2025/month=4/*.parquet') LIMIT 0").fetchall():
    print(f"  {r[0]:<35} {r[1]}")

print("\nGROUND TRUTH columns:")
for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{base}/ground_truth/person_labels/*.parquet') LIMIT 0").fetchall():
    print(f"  {r[0]:<35} {r[1]}")

print("\nTRANSACTIONS columns:")
for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{base}/transactions/*.parquet') LIMIT 0").fetchall():
    print(f"  {r[0]:<35} {r[1]}")

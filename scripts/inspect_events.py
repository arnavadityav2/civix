import duckdb
import os

con = duckdb.connect(":memory:")
datasets = [
    ("cdrs", "cdrs/**/*.parquet"),
    ("transactions", "transactions/**/*.parquet"),
    ("events", "events/**/*.parquet"),
    ("event_participants", "event_participants/**/*.parquet"),
    ("evidence_artifact", "evidence_artifact/**/*.parquet"),
    ("evidence_instance", "evidence_instance/**/*.parquet"),
    ("observation", "observation/**/*.parquet"),
    ("assertions", "assertions/**/*.parquet")
]

for name, rel_path in datasets:
    full_path = os.path.join("demo_world_15k_output", rel_path).replace("\\", "/")
    try:
        cnt = con.execute(f"SELECT COUNT(*) FROM read_parquet('{full_path}')").fetchone()[0]
        cols = con.execute(f"SELECT * FROM read_parquet('{full_path}') LIMIT 1").df().columns.tolist()
        print(f"{name:20s} | Rows: {cnt:10,d} | Columns ({len(cols)}): {cols}")
    except Exception as e:
        print(f"{name:20s} | Error: {e}")

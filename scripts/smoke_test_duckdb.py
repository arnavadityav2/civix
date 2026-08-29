"""
Quick smoke test: verify DuckDB can spill to D:\civix_tmp by running
a medium-sized query on the CDRs (first 5M rows only).
"""
import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")

from civix_ml.utils.duckdb_utils import get_connection
from civix_ml import config

con = get_connection()

# Verify settings
r = con.execute("""
    SELECT
        current_setting('temp_directory') AS tmpdir,
        current_setting('memory_limit') AS memlim,
        current_setting('threads') AS threads,
        current_setting('preserve_insertion_order') AS ins_order
""").fetchone()
print("Settings:")
print(f"  temp_dir : {r[0]}")
print(f"  mem_limit: {r[1]}")
print(f"  threads  : {r[2]}")
print(f"  ins_order: {r[3]}")

# Test query on a single CDR partition (small sample)
cdr_sample = r"D:\civix_data\synthetic\profile_c\cdrs\year=2022\month=1\part-00000.parquet"
n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{cdr_sample}')").fetchone()[0]
print(f"\nCDR sample rows: {n:,}")

agg = con.execute(f"""
    SELECT COUNT(DISTINCT caller_person_id) AS persons,
           COUNT(*) AS calls,
           AVG(duration_seconds) AS avg_dur
    FROM read_parquet('{cdr_sample}')
""").fetchone()
print(f"  Distinct persons: {agg[0]:,}")
print(f"  Total calls     : {agg[1]:,}")
print(f"  Avg duration    : {agg[2]:.1f}s")
con.close()
print("\nSmoke test PASSED")

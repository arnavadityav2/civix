import time
import os
import duckdb
from civix_ml.features.feature_pipeline import run_feature_pipeline, FORBIDDEN_COLUMNS

print("Starting feature pipeline rebuild...")
start_time = time.time()

try:
    merged_path = run_feature_pipeline(skip_existing=False)
    elapsed = time.time() - start_time
    print(f"\nFeature pipeline completed successfully in {elapsed:.2f} seconds.")
    print(f"Output saved to: {merged_path}")
    
    con = duckdb.connect(':memory:')
    df_desc = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{str(merged_path).replace(chr(92), '/')}')").df()
    cols = df_desc['column_name'].tolist()
    
    num_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{str(merged_path).replace(chr(92), '/')}')").fetchone()[0]
    con.close()
    
    print(f"\nFeature matrix rows: {num_rows}")
    print(f"Feature matrix columns: {len(cols)}")
    
    leaked = [c for c in cols if c in FORBIDDEN_COLUMNS or c == 'financial_pattern']
    if leaked:
        print(f"FAILED LEAKAGE GATE: {leaked}")
    else:
        print("PASSED LEAKAGE GATE: 0 forbidden columns found.")
        
    print(f"FORBIDDEN_COLUMNS set: {FORBIDDEN_COLUMNS}")
except Exception as e:
    print(f"\nFAILED: {e}")

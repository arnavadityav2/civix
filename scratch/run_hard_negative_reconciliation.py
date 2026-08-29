import duckdb
import pandas as pd
from pathlib import Path
import json

# Setup paths
V2A_DIR = Path("D:/civix_data/synthetic/profile_v2_v2a")
V2B_DIR = Path("D:/civix_data/synthetic/profile_v2_v2b")
V2C_DIR = Path("D:/civix_data/synthetic/profile_v2_v2c")

# Queries
queries = {
    "v2a_full": f"""
        SELECT 
            COUNT(*) as total_entities,
            SUM(CAST(is_false_positive AS INT)) as hard_negatives
        FROM read_parquet('{V2A_DIR}/ground_truth/person_labels/*.parquet')
    """,
    "v2a_splits": f"""
        SELECT 
            s.split,
            COUNT(*) as total_entities,
            SUM(CAST(l.is_false_positive AS INT)) as hard_negatives
        FROM read_parquet('{V2A_DIR}/ground_truth/person_labels/*.parquet') l
        JOIN read_parquet('{V2A_DIR}/ground_truth/train_val_test_split/*.parquet') s
        ON l.entity_id = s.entity_id
        GROUP BY s.split
    """,
    "v2b_full": f"""
        SELECT 
            COUNT(*) as total_entities,
            SUM(CAST(is_false_positive AS INT)) as hard_negatives
        FROM read_parquet('{V2B_DIR}/ground_truth/person_labels/*.parquet')
    """,
    "v2c_full": f"""
        SELECT 
            COUNT(*) as total_entities,
            SUM(CAST(is_false_positive AS INT)) as hard_negatives
        FROM read_parquet('{V2C_DIR}/ground_truth/person_labels/*.parquet')
    """
}

results = {}
for name, query in queries.items():
    try:
        df = duckdb.query(query).to_df()
        if name == "v2a_splits":
            results[name] = df.to_dict('records')
        else:
            results[name] = df.iloc[0].to_dict()
    except Exception as e:
        results[name] = {"error": str(e)}

print(json.dumps(results, indent=2))

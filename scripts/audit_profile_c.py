import os
import glob
import json
import duckdb
from datetime import datetime

PROFILE_DIR = r"D:\civix_data\synthetic\profile_c"
OUTPUT_JSON = r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0\docs\phase3a\dataset_audit.json"

os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)

con = duckdb.connect(':memory:')
audit = {
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "profile": "Profile C",
    "directory": PROFILE_DIR,
    "tables": {},
    "manifest": None,
    "ground_truth_isolation": {},
    "splits": {},
    "label_distributions": {}
}

print(f"Starting Profile C Dataset Audit at {PROFILE_DIR}...")

# 1. Read Manifest
manifest_path = os.path.join(PROFILE_DIR, "manifest.json")
if os.path.exists(manifest_path):
    with open(manifest_path, 'r') as f:
        audit["manifest"] = json.load(f)
        print("Loaded manifest.json")

# 2. Map all parquet directories
table_dirs = []
for root, dirs, files in os.walk(PROFILE_DIR):
    if any(f.endswith('.parquet') for f in files):
        table_dirs.append(root.replace('\\', '/'))

table_dirs = sorted(list(set([d for d in table_dirs if '=' not in d.split('/')[-1]])))
if len(table_dirs) == 0:
    # Handle partitioned directories like cdrs/year=2025/month=1
    all_files = glob.glob(f"{PROFILE_DIR}/**/*.parquet", recursive=True)
    parents = set(os.path.dirname(f).replace('\\', '/') for f in all_files)
    table_dirs = sorted(list(parents))

# Deduplicate to base table names
base_tables = set()
for d in table_dirs:
    rel_path = os.path.relpath(d, PROFILE_DIR).replace('\\', '/')
    if rel_path.startswith('cdrs'):
        base_tables.add('cdrs')
    elif rel_path.startswith('transactions'):
        base_tables.add('transactions')
    else:
        base_tables.add(rel_path)

print(f"Found {len(base_tables)} logical tables.")

for t in sorted(base_tables):
    print(f"Auditing table: {t}...")
    if t in ['cdrs', 'transactions']:
        glob_path = f"{PROFILE_DIR}/{t}/**/*.parquet".replace('\\', '/')
    else:
        glob_path = f"{PROFILE_DIR}/{t}/*.parquet".replace('\\', '/')
        
    try:
        # Schema
        schema_res = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{glob_path}', union_by_name=True)").fetchall()
        schema = {col[0]: col[1] for col in schema_res}
        
        # Row count
        count_res = con.execute(f"SELECT COUNT(*) FROM read_parquet('{glob_path}', union_by_name=True)").fetchone()[0]
        
        # Null counts (sample first 5 columns to keep it fast)
        null_counts = {}
        cols_to_check = [col[0] for col in schema_res[:5]]
        null_sql = ", ".join([f"COUNT(*) - COUNT({c}) AS {c}_nulls" for c in cols_to_check])
        null_res = con.execute(f"SELECT {null_sql} FROM read_parquet('{glob_path}', union_by_name=True)").fetchone()
        for i, c in enumerate(cols_to_check):
            null_counts[c] = null_res[i]
            
        audit["tables"][t] = {
            "row_count": count_res,
            "schema": schema,
            "null_rates": {k: round(v/count_res, 4) if count_res > 0 else 0 for k, v in null_counts.items()}
        }
        
        # Timestamp ranges
        for col, dtype in schema.items():
            if 'timestamp' in col.lower() or dtype in ['TIMESTAMP', 'DATE']:
                trange = con.execute(f"SELECT MIN({col}), MAX({col}) FROM read_parquet('{glob_path}', union_by_name=True)").fetchone()
                audit["tables"][t]["timestamp_range"] = {col: [str(trange[0]), str(trange[1])]}
                
    except Exception as e:
        print(f"Error auditing {t}: {e}")

# 3. Splits & Distributions
print("Auditing labels and splits...")
try:
    split_path = f"{PROFILE_DIR}/ground_truth/train_val_test_split/*.parquet".replace('\\', '/')
    splits = con.execute(f"SELECT split, COUNT(*) FROM read_parquet('{split_path}') GROUP BY split").fetchall()
    audit["splits"] = {s[0]: s[1] for s in splits}
    
    label_path = f"{PROFILE_DIR}/ground_truth/person_labels/*.parquet".replace('\\', '/')
    labels = con.execute(f"SELECT scenario_class, COUNT(*) FROM read_parquet('{label_path}') GROUP BY scenario_class").fetchall()
    audit["label_distributions"] = {l[0]: l[1] for l in labels}
    
    families = con.execute(f"SELECT scenario_family, COUNT(*) FROM read_parquet('{label_path}') GROUP BY scenario_family").fetchall()
    audit["family_distributions"] = {f[0]: f[1] for f in families}
    
except Exception as e:
    print(f"Error auditing ground truth: {e}")

# 4. Leakage Audit
print("Running automated leakage checks...")
try:
    # 4a. Check if 'scenario_class' or 'is_positive_label' leaked into ML features
    features_path = f"{PROFILE_DIR}/ml_features/person_communication_features.parquet".replace('\\', '/')
    feat_schema = [c[0].lower() for c in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{features_path}')").fetchall()]
    
    leakage_terms = ['scenario', 'risk_score_gt', 'is_positive', 'ground_truth', 'false_positive']
    leaks = [c for c in feat_schema if any(t in c for t in leakage_terms)]
    audit["ground_truth_isolation"]["ml_features_leaks"] = leaks
    audit["ground_truth_isolation"]["passed"] = len(leaks) == 0
except Exception as e:
    print(f"Error checking leakage: {e}")


with open(OUTPUT_JSON, 'w') as f:
    json.dump(audit, f, indent=2)

print(f"\nAudit complete. JSON saved to {OUTPUT_JSON}")

import os
import json
import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from pathlib import Path

print("==================================================")
print("CIVIX PHASE 5 CHUNK 3: DISTRIBUTION SHIFT AUDIT")
print("==================================================")

METADATA_PATH = r"D:\civix_data\models\experiments\behavioral_xgboost_20260829T202007.json"
with open(METADATA_PATH, 'r') as f:
    meta = json.load(f)
EXPECTED_FEATURES = meta['features']
# Filter out one-hot features for numerical shift analysis
NUMERICAL_FEATURES = [f for f in EXPECTED_FEATURES if not f.startswith("gender_") and not f.startswith("occupation_") and not f.startswith("home_region_")]

def get_stats(universe_dir: str):
    feat_path = Path(universe_dir) / "features_v1" / "features_merged.parquet"
    if not feat_path.exists():
        return None
        
    df = pq.read_table(str(feat_path)).to_pandas()
    stats = []
    for col in NUMERICAL_FEATURES:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors='coerce').fillna(0)
            stats.append({
                "feature": col,
                "mean": series.mean(),
                "std": series.std(),
                "median": series.median(),
                "min": series.min(),
                "max": series.max()
            })
    return pd.DataFrame(stats)

print("Calculating V2A baseline stats...")
v2a_stats = get_stats(r"D:\civix_data\synthetic\profile_v2_v2a")

print("Calculating V2B stats...")
v2b_stats = get_stats(r"D:\civix_data\synthetic\profile_v2_v2b")

print("Calculating V2C stats...")
v2c_stats = get_stats(r"D:\civix_data\synthetic\profile_v2_v2c")

if v2a_stats is not None and v2b_stats is not None and v2c_stats is not None:
    v2a_stats.set_index("feature", inplace=True)
    v2b_stats.set_index("feature", inplace=True)
    v2c_stats.set_index("feature", inplace=True)
    
    compare = pd.DataFrame()
    compare["V2A_mean"] = v2a_stats["mean"].round(4)
    compare["V2B_mean"] = v2b_stats["mean"].round(4)
    compare["V2C_mean"] = v2c_stats["mean"].round(4)
    
    # Calculate simple relative mean shift
    compare["V2B_shift_%"] = (((compare["V2B_mean"] - compare["V2A_mean"]) / (compare["V2A_mean"].abs() + 1e-9)) * 100).round(2)
    compare["V2C_shift_%"] = (((compare["V2C_mean"] - compare["V2A_mean"]) / (compare["V2A_mean"].abs() + 1e-9)) * 100).round(2)
    
    compare.to_csv("scratch/chunk3_distribution_shift.csv")
    print("Saved distribution shift summary to scratch/chunk3_distribution_shift.csv")
    
    # Print the top 10 most shifted features in V2B
    print("\n[V2B] Top 10 Most Shifted Features (by absolute %):")
    v2b_shift = compare.copy()
    v2b_shift["abs_shift"] = v2b_shift["V2B_shift_%"].abs()
    print(v2b_shift.sort_values(by="abs_shift", ascending=False)[["V2A_mean", "V2B_mean", "V2B_shift_%"]].head(10).to_string())

    print("\n[V2C] Top 10 Most Shifted Features (by absolute %):")
    v2c_shift = compare.copy()
    v2c_shift["abs_shift"] = v2c_shift["V2C_shift_%"].abs()
    print(v2c_shift.sort_values(by="abs_shift", ascending=False)[["V2A_mean", "V2C_mean", "V2C_shift_%"]].head(10).to_string())

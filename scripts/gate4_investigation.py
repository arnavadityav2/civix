"""
GATE 4 Investigation — Diagnose suspiciously perfect PR-AUC=1.0.
Check whether:
1. The top features separate classes unrealistically
2. A generator artifact exists (e.g., all confirmed_pattern have identical min_duration_sec)
3. The separation is expected given the synthetic generator's design
"""
import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from pathlib import Path
import pandas as pd
from civix_ml.features.feature_pipeline import load_training_data

merged = Path(r"D:\civix_data\synthetic\profile_c\features_v1\features_merged.parquet")
X, y, y_sc = load_training_data(merged, split="TRAIN")

df = X.copy()
df["label"] = y.values
df["scenario"] = y_sc.values

print("=" * 60)
print("GATE 4: Synthetic Artifact Investigation")
print("=" * 60)

# 1. Distribution of top feature by label class
print("\n--- min_duration_sec by scenario class ---")
print(df.groupby("scenario")["min_duration_sec"].describe().round(2))

print("\n--- max_duration_sec by scenario class ---")
print(df.groupby("scenario")["max_duration_sec"].describe().round(2))

print("\n--- avg_duration_sec by scenario class ---")
print(df.groupby("scenario")["avg_duration_sec"].describe().round(2))

print("\n--- total_txns by scenario class ---")
print(df.groupby("scenario")["total_txns"].describe().round(2))

# 2. Check if top feature values overlap between confirmed_pattern and normal
cp = df[df["scenario"] == "confirmed_pattern"]["min_duration_sec"]
normal = df[df["scenario"] == "normal"]["min_duration_sec"]

print(f"\n--- Overlap analysis: min_duration_sec ---")
print(f"  confirmed_pattern: min={cp.min():.1f}, max={cp.max():.1f}, mean={cp.mean():.1f}")
print(f"  normal:            min={normal.min():.1f}, max={normal.max():.1f}, mean={normal.mean():.1f}")

overlap_lo = max(cp.min(), normal.min())
overlap_hi = min(cp.max(), normal.max())
print(f"  Overlap range: [{overlap_lo:.1f}, {overlap_hi:.1f}]")
print(f"  Overlap exists: {overlap_lo < overlap_hi}")

# 3. Persons with ZERO calls — do they exist?
zero_calls = (df["total_calls"] == 0).sum()
print(f"\n--- Zero-call persons: {zero_calls:,} / {len(df):,} ---")
if zero_calls > 0:
    print(df[df["total_calls"] == 0]["scenario"].value_counts())

# 4. Check if any feature is a perfect predictor
print("\n--- Checking for perfect single-feature separators ---")
for col in ["min_duration_sec", "max_duration_sec", "total_txns", "avg_txn_amount"]:
    corr = abs(df[col].corr(df["label"]))
    print(f"  {col}: |corr with label| = {corr:.4f}")

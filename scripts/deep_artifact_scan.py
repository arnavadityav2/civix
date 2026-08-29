"""
Deep artifact investigation — check RANGE OVERLAP between classes, not just CV.
A feature can have high within-class variance but STILL perfectly separate classes
if the class ranges [min, max] don't overlap at all.
"""
import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from pathlib import Path
import pandas as pd
import numpy as np
from civix_ml.features.feature_pipeline import load_training_data

merged = Path(r"D:\civix_data\synthetic\profile_c\features_v1\features_merged.parquet")
X, y, y_sc = load_training_data(merged, split="TRAIN")

df = X.copy()
df["label"] = y.values
df["scenario"] = y_sc.values

numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()

print("=" * 80)
print("DEEP ARTIFACT SCAN — Range Overlap Between confirmed_pattern vs normal")
print("NON-OVERLAP = feature perfectly separates classes on its own range")
print("=" * 80)

no_overlap = []
partial_overlap = []
full_overlap = []

cp    = df[df["scenario"] == "confirmed_pattern"]
norm  = df[df["scenario"] == "normal"]
susp  = df[df["scenario"] == "suspicious"]
fp    = df[df["scenario"] == "false_positive"]

for col in numeric_cols:
    # Check overlap between confirmed_pattern and normal (the key discriminative pair)
    cp_min, cp_max   = cp[col].min(), cp[col].max()
    nr_min, nr_max   = norm[col].min(), norm[col].max()
    sp_min, sp_max   = susp[col].min(), susp[col].max()

    overlap_lo = max(cp_min, nr_min)
    overlap_hi = min(cp_max, nr_max)
    has_overlap_nr = overlap_lo <= overlap_hi

    overlap_lo2 = max(cp_min, sp_min)
    overlap_hi2 = min(cp_max, sp_max)
    has_overlap_sp = overlap_lo2 <= overlap_hi2

    if not has_overlap_nr and not has_overlap_sp:
        no_overlap.append(col)
        flag = "NO_OVERLAP"
    elif not has_overlap_nr or not has_overlap_sp:
        partial_overlap.append(col)
        flag = "PARTIAL"
    else:
        full_overlap.append(col)
        flag = "overlap"

    print(f"  {flag:12s}  {col:<35s}  "
          f"CP=[{cp_min:.1f},{cp_max:.1f}] NR=[{nr_min:.1f},{nr_max:.1f}] SP=[{sp_min:.1f},{sp_max:.1f}]")

print(f"\n{'='*80}")
print(f"NO_OVERLAP features (perfect class separators — additional artifacts): {len(no_overlap)}")
for c in no_overlap:
    print(f"  - {c}")

print(f"\nPARTIAL overlap (separates some class pairs): {len(partial_overlap)}")
for c in partial_overlap:
    print(f"  - {c}")

print(f"\nFull overlap (genuinely ambiguous): {len(full_overlap)}")
for c in full_overlap:
    print(f"  - {c}")

print(f"\n--- CONCLUSION ---")
print(f"Features with genuine ambiguity (overlap between ALL class pairs): {len(full_overlap)}")
print(f"These are the ONLY features that cannot trivially separate classes.")

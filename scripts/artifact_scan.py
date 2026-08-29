"""
Identify all generator-artifact features by checking within-class variance.
Any feature with near-zero variance across 17k+ persons of the same class
was hardcoded by the generator and is trivially discriminative.
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
df["scenario"] = y_sc.values

numeric_cols = X.select_dtypes(include=[np.number]).columns.tolist()

print("=" * 70)
print("GATE 4 ARTIFACT SCAN — Within-class coefficient of variation (CV)")
print("CV = std/mean per class. CV near 0 = generator artifact.")
print("=" * 70)

artifact_cols = []
ARTIFACT_CV_THRESHOLD = 0.05  # less than 5% CV → suspect

for col in numeric_cols:
    class_stats = df.groupby("scenario")[col].agg(["std", "mean"]).fillna(0)
    # CV for each class
    cvs = []
    for sc in ["confirmed_pattern", "normal", "suspicious"]:
        if sc in class_stats.index:
            m = class_stats.loc[sc, "mean"]
            s = class_stats.loc[sc, "std"]
            cv = s / (abs(m) + 1e-9)
            cvs.append(cv)
    max_cv = max(cvs) if cvs else 1.0
    flag = "ARTIFACT" if max_cv < ARTIFACT_CV_THRESHOLD else "ok"
    if flag == "ARTIFACT":
        artifact_cols.append(col)
    print(f"  {flag:8s}  {col:<35s}  max_CV={max_cv:.4f}")

print(f"\n{'='*70}")
print(f"ARTIFACTS FOUND: {len(artifact_cols)}")
for c in artifact_cols:
    print(f"  - {c}")
print(f"\nThese features MUST be excluded from training.")
print(f"They give perfect class separation only because the generator hardcoded")
print(f"fixed values per scenario_class — NOT because of real-world behavioral patterns.")

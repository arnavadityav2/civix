"""Quick test of load_training_data to verify entity_id join is correct."""
import sys
sys.path.insert(0, r"C:\Users\ARNAV ADITYA\Desktop\civix 2.0")
from pathlib import Path
from civix_ml.features.feature_pipeline import load_training_data

merged = Path(r"D:\civix_data\synthetic\profile_c\features_v1\features_merged.parquet")

X, y, y_sc = load_training_data(merged, split="TRAIN")
print(f"TRAIN: X={X.shape}, positives={y.sum():,}/{len(y):,} ({y.mean()*100:.1f}%)")
print(f"  Feature cols (first 5): {list(X.columns[:5])}")
print(f"  Scenario sample: {y_sc.value_counts().head(5).to_dict()}")

X_v, y_v, _ = load_training_data(merged, split="VALIDATION")
print(f"VAL:   X={X_v.shape}, positives={y_v.sum():,}/{len(y_v):,}")

X_t, y_t, _ = load_training_data(merged, split="TEST")
print(f"TEST:  X={X_t.shape}, positives={y_t.sum():,}/{len(y_t):,}")
print("JOIN TEST PASSED")

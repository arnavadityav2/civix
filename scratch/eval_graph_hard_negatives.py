import os
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from civix_ml import config
from civix_ml.models.graph_baselines import load_graph_features, load_combined_features
import pickle

print("=== Phase 5 Chunk 2: Hard Negative Evaluation (Graph & Combined) ===")
# 1. Load Hard Negative ground truth
con = duckdb.connect(":memory:")
from civix_ml.graph.schema import GRAPH_FEATURES_DIR
feat_path = str(GRAPH_FEATURES_DIR / "graph_features.parquet").replace("\\", "/")
labs_path = config.LABELS_GLOB.replace("\\", "/")
splits_path = config.SPLITS_GLOB.replace("\\", "/")

fp_df = con.execute(f"""
    SELECT f.person_id, l.is_false_positive, l.scenario_class
    FROM read_parquet('{feat_path}') f
    JOIN read_parquet('{splits_path}') s ON s.entity_id = f.person_id
    JOIN read_parquet('{labs_path}') l ON l.entity_id = f.person_id
    WHERE s.split = 'TEST'
""").df()
con.close()

# Keep ordering aligned with TEST set
print("Loading TEST splits...")
X_test_g, y_test_g, _ = load_graph_features("TEST")
X_test_c, y_test_c, _ = load_combined_features("TEST")

# Verify alignment
assert len(X_test_g) == len(fp_df), "Mismatch in test sizes!"

# True adversarial positives
is_fp = (fp_df["is_false_positive"] == 1).values
total_fps = is_fp.sum()

def eval_hard_negatives(model_name, feature_type, X, y):
    print(f"\n--- {feature_type.upper()} Model: {model_name} ---")
    # Load model from registry
    # Since we train random_forest, find the latest rf model
    import glob
    model_dirs = sorted(glob.glob(str(config.MODELS_DIR / "registry" / f"{feature_type}_{model_name}_*")), reverse=True)
    if not model_dirs:
        print(f"Model not found for {feature_type} {model_name}.")
        return
    
    import joblib
    model = joblib.load(Path(model_dirs[0]) / "model.pkl")
        
    probs = model.predict_proba(X)[:, 1]
    
    k_5pct = int(len(y) * 0.05)
    sorted_indices = np.argsort(probs)[::-1]
    
    # How many of top 5% are false_positive?
    top_5pct_fp = is_fp[sorted_indices[:k_5pct]]
    count_fp = top_5pct_fp.sum()
    
    print(f"Top 5% alerts that are Hard Negatives: {count_fp} / {k_5pct} ({(count_fp/k_5pct)*100:.1f}%)")
    print(f"Total False Positives caught in Top 5%: {count_fp} / {total_fps} ({(count_fp/total_fps)*100:.1f}%)")

eval_hard_negatives("random_forest", "graph", X_test_g, y_test_g)
eval_hard_negatives("random_forest", "combined", X_test_c, y_test_c)
print("\nDone.")

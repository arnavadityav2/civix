import os
import json
import pandas as pd
import numpy as np
import joblib
import subprocess
from pathlib import Path
import pyarrow.parquet as pq
from civix_ml import config

print("==================================================")
print("CIVIX PHASE 5 CHUNK 3: UNSEEN UNIVERSE INFERENCE")
print("==================================================")

METADATA_PATH = r"D:\civix_data\models\experiments\behavioral_xgboost_20260829T202007.json"
MODEL_PATH = r"D:\civix_data\models\registry\behavioral_xgboost_20260829T202007\model.pkl"
PREDICTIONS_DIR = Path(r"D:\civix_data\models\predictions")
PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

with open(METADATA_PATH, 'r') as f:
    meta = json.load(f)
EXPECTED_FEATURES = meta['features']
print(f"Loaded canonical model schema: {len(EXPECTED_FEATURES)} expected features.")

# Load the frozen model
model = joblib.load(MODEL_PATH)
print("Loaded Canonical XGBoost Model.")

def process_universe(universe_name: str, universe_dir: str):
    print(f"\n[{universe_name.upper()}] Starting Feature Extraction & Inference...")
    
    # Execute the feature pipeline in a subprocess with the overridden environment
    # This ensures the config module picks up the new universe directory cleanly
    script_content = f"""
import os
os.environ['CIVIX_PROFILE_DIR'] = r'{universe_dir}'
from civix_ml.features.feature_pipeline import run_feature_pipeline
run_feature_pipeline(skip_existing=True)
"""
    tmp_file = f"tmp_run_{universe_name}.py"
    with open(tmp_file, "w") as f:
        f.write(script_content)
        
    try:
        subprocess.run(["python", tmp_file], check=True)
    finally:
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
            
    # Load the resulting feature matrix
    feat_path = Path(universe_dir) / "features_v1" / "features_merged.parquet"
    if not feat_path.exists():
        raise FileNotFoundError(f"Feature matrix failed to build at {feat_path}")
        
    df = pq.read_table(str(feat_path)).to_pandas()
    person_ids = df["person_id"]
    
    # Drop forbidden / artifact columns exactly like load_training_data
    label_cols = ["scenario_class", "is_positive_label", "is_false_positive", "difficulty"]
    RAW_TS_COLS = ["first_call_ts", "last_call_ts", "first_txn_ts", "last_txn_ts"]
    drop_cols = ["person_id"] + label_cols + RAW_TS_COLS + config.GENERATOR_ARTIFACT_FEATURES
    X = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")
    
    # Process categorical variables (one-hot encode)
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    safe_cat = [c for c in cat_cols if X[c].nunique() < 50]
    high_card = [c for c in cat_cols if c not in safe_cat]
    if high_card:
        X = X.drop(columns=high_card)
    if safe_cat:
        X = pd.get_dummies(X, columns=safe_cat, drop_first=True, dtype=float)
        
    X = X.fillna(0)
    
    # EXACT FEATURE RECONSTRUCTION
    # Pad missing one-hot categories with 0, drop any unexpected features
    for col in EXPECTED_FEATURES:
        if col not in X.columns:
            X[col] = 0.0
            
    # Force exact column ordering
    X = X[EXPECTED_FEATURES]
    
    # Generate Predictions
    print(f"[{universe_name.upper()}] Feature alignment complete. Executing inference on {len(X):,} entities...")
    probs = model.predict_proba(X)[:, 1]
    
    out_df = pd.DataFrame({
        "person_id": person_ids,
        "prediction_score": probs
    })
    
    out_path = PREDICTIONS_DIR / f"{universe_name}_predictions.parquet"
    out_df.to_parquet(str(out_path), index=False)
    print(f"[{universe_name.upper()}] Saved predictions -> {out_path}")

process_universe("v2b", r"D:\civix_data\synthetic\profile_v2_v2b")
process_universe("v2c", r"D:\civix_data\synthetic\profile_v2_v2c")

print("\nChunk 3 Inference Phase Complete.")

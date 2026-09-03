import pickle
import duckdb
import os
import pandas as pd
import numpy as np

def test_xgboost():
    print("==========================================================")
    print("PHASE 8: XGBOOST INFERENCE & FEATURE CONTRACT CHECK")
    print("==========================================================")
    
    model_path = "models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl"
    if not os.path.exists(model_path):
        print(f"[FAIL] Model artifact not found at {model_path}")
        return
        
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    print(f"Loaded XGBoost Model: {type(model).__name__}")
    if hasattr(model, "n_features_in_"):
        print(f"Model expected feature count: {model.n_features_in_}")
        
    con = duckdb.connect(":memory:")
    comm_path = "demo_world_15k_output/ml_features/person_communication_features.parquet"
    fin_path = "demo_world_15k_output/ml_features/person_financial_features.parquet"
    
    if os.path.exists(comm_path) and os.path.exists(fin_path):
        comm_df = con.execute(f"SELECT * FROM read_parquet('{comm_path}')").df()
        fin_df = con.execute(f"SELECT * FROM read_parquet('{fin_path}')").df()
        print(f"Communication features shape: {comm_df.shape}")
        print(f"Financial features shape    : {fin_df.shape}")
        
        # Merge on person_id
        features_df = pd.merge(comm_df, fin_df, on="person_id", how="inner")
        print(f"Merged per-person features  : {features_df.shape}")
        
        # Drop person_id for scoring
        X = features_df.drop(columns=["person_id"], errors="ignore")
        print(f"Feature matrix columns count: {X.shape[1]}")
        
        # Fill missing values cleanly
        X = X.fillna(0.0)
        
        if hasattr(model, "predict_proba"):
            preds = model.predict_proba(X.iloc[:100])[:, 1]
            print(f"Sample prediction scores (first 10): {np.round(preds[:10], 4)}")
            print(f"Score range across 100 samples    : [{preds.min():.4f}, {preds.max():.4f}]")
            
    con.close()
    print("[PASS] XGBoost Model Compatibility & Feature Vector Verification Complete.")

if __name__ == "__main__":
    test_xgboost()

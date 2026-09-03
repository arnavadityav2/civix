import joblib
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

model_path = 'models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl'
model = joblib.load(model_path)

print(f"Model Class: {type(model).__name__}")
features = list(model.feature_names_in_)
print(f"Expected Feature Count: {len(features)}")
print(f"feature_names_in_ exists: {hasattr(model, 'feature_names_in_')}")

print("\n--- EXACT FEATURE ORDERING ---")
for i, f in enumerate(features):
    print(f"{i}: {f}")

print("\n--- FEATURE IMPORTANCES (Weight/Gain) ---")
try:
    booster = model.get_booster()
    gains = booster.get_score(importance_type='gain')
    weights = booster.get_score(importance_type='weight')
    
    importance_df = pd.DataFrame({
        'Feature': features,
        'Gain': [gains.get(f, 0.0) for f in features],
        'Weight': [weights.get(f, 0.0) for f in features]
    })
    importance_df = importance_df.sort_values(by='Gain', ascending=False)
    print(importance_df.to_string(index=False))
except Exception as e:
    print(f"Could not extract importance: {e}")

import joblib
import pandas as pd
import json
import numpy as np

# Load the model
model_path = "models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl"
print(f"Loading model from {model_path}...")
model = joblib.load(model_path)
print(f"Model loaded. Expected features: {len(model.feature_names_in_)}")

with open("parity_results.json", "r") as f:
    results = json.load(f)

# Build Case A (PostgreSQL Vector)
case_a = {}
for r in results:
    case_a[r['feature_name']] = float(r['postgres_value'])

df_a = pd.DataFrame([case_a])[model.feature_names_in_]
prob_a = model.predict_proba(df_a)[0][1]

# Build Case B (Offline Vector for GAPs only)
case_b = case_a.copy()
# The known GAPs as defined by the report
gaps = ['txn_type_diversity', 'amount_concentration', 'unique_regions', 'geo_spread_degrees']
for r in results:
    if r['feature_name'] in gaps:
        case_b[r['feature_name']] = float(r['offline_value'])

df_b = pd.DataFrame([case_b])[model.feature_names_in_]
prob_b = model.predict_proba(df_b)[0][1]

print("\n--- MODEL IMPACT EXPERIMENT ---")
print(f"Case A (PostgreSQL):       {prob_a:.4f}")
print(f"Case B (Offline GAPs):     {prob_b:.4f}")
print(f"Absolute Impact Delta:     {abs(prob_a - prob_b):.4f}")

# Build Case C (Material discrepancies replaced one by one)
discrepancies = [r for r in results if r['semantic_status'] == 'FAIL']
print("\n--- CASE C: ISOLATED MATERIAL DISCREPANCIES ---")
if not discrepancies:
    print("No material discrepancies to evaluate.")
else:
    for d in discrepancies:
        fname = d['feature_name']
        case_c = case_a.copy()
        case_c[fname] = float(d['offline_value'])
        df_c = pd.DataFrame([case_c])[model.feature_names_in_]
        prob_c = model.predict_proba(df_c)[0][1]
        print(f"Reverting {fname:<25} | Postgres: {d['postgres_value']:<10.4f} -> Offline: {d['offline_value']:<10.4f} | New Prob: {prob_c:.4f} | Delta: {abs(prob_a - prob_c):.4f}")

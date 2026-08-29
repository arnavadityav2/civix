import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import json
from pathlib import Path
from civix_ml.evaluation.metrics import evaluate

print("==================================================")
print("CIVIX PHASE 5 CHUNK 3: UNSEEN UNIVERSE EVALUATION")
print("==================================================")

PREDICTIONS_DIR = Path(r"D:\civix_data\models\predictions")

def load_ground_truth(universe_dir: str):
    labels_glob = str(Path(universe_dir) / "ground_truth" / "person_labels" / "*.parquet")
    import duckdb
    con = duckdb.connect()
    df = con.execute(f"SELECT entity_id as person_id, is_positive_label, is_false_positive FROM read_parquet('{labels_glob}')").df()
    con.close()
    return df

def run_evaluation(universe_name: str, universe_dir: str):
    print(f"\n[{universe_name.upper()}] Loading predictions and ground truth...")
    pred_file = PREDICTIONS_DIR / f"{universe_name}_predictions.parquet"
    if not pred_file.exists():
        raise FileNotFoundError(f"Missing {pred_file}")
        
    preds = pd.read_parquet(pred_file)
    gt = load_ground_truth(universe_dir)
    
    df = pd.merge(preds, gt, on="person_id", how="inner")
    print(f"[{universe_name.upper()}] Evaluating {len(df):,} matching entities.")
    
    y_true = df["is_positive_label"].astype(int).values
    y_scores = df["prediction_score"].values
    
    # Standard metrics
    metrics = evaluate(y_true, y_scores, model_name=f"behavioral_xgboost_{universe_name}")
    
    # Hard Negative Evaluation
    # We want to see how many "is_false_positive" == True entities end up in the top 1% and 5%
    k_1pct = max(1, int(len(df) * 0.01))
    k_5pct = max(1, int(len(df) * 0.05))
    
    df_sorted = df.sort_values(by="prediction_score", ascending=False).reset_index(drop=True)
    
    top_1_df = df_sorted.head(k_1pct)
    top_5_df = df_sorted.head(k_5pct)
    
    total_hard_negatives = int(df["is_false_positive"].sum())
    top_1_hn = int(top_1_df["is_false_positive"].sum())
    top_5_hn = int(top_5_df["is_false_positive"].sum())
    
    metrics["total_hard_negatives"] = total_hard_negatives
    metrics["top_1pct_hard_negatives"] = top_1_hn
    metrics["top_1pct_hard_negative_rate"] = top_1_hn / max(total_hard_negatives, 1)
    metrics["top_1pct_budget_occupied"] = top_1_hn / max(k_1pct, 1)
    
    metrics["top_5pct_hard_negatives"] = top_5_hn
    metrics["top_5pct_hard_negative_rate"] = top_5_hn / max(total_hard_negatives, 1)
    metrics["top_5pct_budget_occupied"] = top_5_hn / max(k_5pct, 1)
    
    print(f"[{universe_name.upper()}] Hard Negatives in Top 1%: {top_1_hn} ({metrics['top_1pct_budget_occupied']:.1%} of budget)")
    print(f"[{universe_name.upper()}] Hard Negatives in Top 5%: {top_5_hn} ({metrics['top_5pct_budget_occupied']:.1%} of budget)")
    
    return metrics

metrics_v2b = run_evaluation("v2b", r"D:\civix_data\synthetic\profile_v2_v2b")
metrics_v2c = run_evaluation("v2c", r"D:\civix_data\synthetic\profile_v2_v2c")

out_b = "scratch/chunk3_v2b_metrics.json"
out_c = "scratch/chunk3_v2c_metrics.json"

with open(out_b, "w") as f:
    json.dump(metrics_v2b, f, indent=2)
with open(out_c, "w") as f:
    json.dump(metrics_v2c, f, indent=2)

print(f"\nChunk 3 Evaluation Complete. Metrics dumped to {out_b} and {out_c}.")

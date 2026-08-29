import pandas as pd
import numpy as np
import json
from pathlib import Path
from sklearn.metrics import roc_auc_score, average_precision_score

PREDICTIONS_DIR = Path(r"D:\civix_data\models\predictions")

def load_ground_truth(universe_dir: str):
    labels_glob = str(Path(universe_dir) / "ground_truth" / "person_labels" / "*.parquet")
    import duckdb
    con = duckdb.connect()
    df = con.execute(f"SELECT entity_id as person_id, is_positive_label, is_false_positive FROM read_parquet('{labels_glob}')").df()
    con.close()
    return df

def precision_at_k(y_true, y_scores, k_pct):
    k = max(1, int(len(y_true) * k_pct / 100))
    top_k_idx = np.argsort(y_scores)[::-1][:k]
    return y_true[top_k_idx].mean()

def compute_bootstrap_cis(df, n_iterations=1000, seed=42):
    np.random.seed(seed)
    n_size = len(df)
    
    results = {
        "roc_auc": [],
        "pr_auc": [],
        "p_at_1": [],
        "p_at_5": []
    }
    
    y_true_full = df["is_positive_label"].astype(int).values
    y_scores_full = df["prediction_score"].values
    
    print(f"  Starting {n_iterations} bootstrap replicates...")
    for i in range(n_iterations):
        if i % 200 == 0 and i > 0:
            print(f"    ... {i} replicates done")
            
        # Draw random indices with replacement
        indices = np.random.choice(n_size, size=n_size, replace=True)
        y_t = y_true_full[indices]
        y_s = y_scores_full[indices]
        
        # Only compute if we have both classes
        if len(np.unique(y_t)) > 1:
            results["roc_auc"].append(roc_auc_score(y_t, y_s))
            results["pr_auc"].append(average_precision_score(y_t, y_s))
            results["p_at_1"].append(precision_at_k(y_t, y_s, 1.0))
            results["p_at_5"].append(precision_at_k(y_t, y_s, 5.0))
            
    cis = {}
    for metric, values in results.items():
        if values:
            lower = np.percentile(values, 2.5)
            upper = np.percentile(values, 97.5)
            cis[metric] = {"lower": round(lower, 4), "upper": round(upper, 4), "mean": round(np.mean(values), 4)}
    return cis

def audit_hard_negatives(df, universe_name):
    print(f"\n[{universe_name}] Hard Negative Score Distribution Audit")
    
    tp = df[df["is_positive_label"] == True]["prediction_score"]
    tn = df[(df["is_positive_label"] == False) & (df["is_false_positive"] == False)]["prediction_score"]
    hn = df[df["is_false_positive"] == True]["prediction_score"]
    
    print(f"  True Positives (N={len(tp)}): Mean={tp.mean():.4f}, Median={tp.median():.4f}")
    print(f"  Ordinary Negatives (N={len(tn)}): Mean={tn.mean():.4f}, Median={tn.median():.4f}")
    print(f"  Hard Negatives (N={len(hn)}): Mean={hn.mean():.4f}, Median={hn.median():.4f}")
    
    if len(hn) > 0:
        print(f"  Hard Negatives Stats:")
        print(f"    Min: {hn.min():.4f}, Max: {hn.max():.4f}, Std: {hn.std():.4f}")
        print(f"    90th pct: {hn.quantile(0.90):.4f}")
        print(f"    95th pct: {hn.quantile(0.95):.4f}")
        print(f"    99th pct: {hn.quantile(0.99):.4f}")
        
        # Rank within the FULL population
        df_sorted = df.sort_values(by="prediction_score", ascending=False).reset_index(drop=True)
        df_sorted["rank"] = df_sorted.index + 1
        
        hn_ranks = df_sorted[df_sorted["is_false_positive"] == True]["rank"]
        
        n_total = len(df)
        print(f"    Max overall rank: {hn_ranks.min()} (out of {n_total})")
        print(f"    Number in Top 0.1% (Rank <= {int(n_total*0.001)}): {len(hn_ranks[hn_ranks <= int(n_total*0.001)])}")
        print(f"    Number in Top 0.5% (Rank <= {int(n_total*0.005)}): {len(hn_ranks[hn_ranks <= int(n_total*0.005)])}")
        print(f"    Number in Top 1% (Rank <= {int(n_total*0.01)}): {len(hn_ranks[hn_ranks <= int(n_total*0.01)])}")
        print(f"    Number in Top 5% (Rank <= {int(n_total*0.05)}): {len(hn_ranks[hn_ranks <= int(n_total*0.05)])}")
        
def process_universe(universe_name, universe_dir):
    print(f"\nProcessing {universe_name}...")
    pred_file = PREDICTIONS_DIR / f"{universe_name}_predictions.parquet"
    preds = pd.read_parquet(pred_file)
    gt = load_ground_truth(universe_dir)
    df = pd.merge(preds, gt, on="person_id", how="inner")
    
    audit_hard_negatives(df, universe_name)
    cis = compute_bootstrap_cis(df)
    
    print(f"  Bootstrap CIs:")
    for m, c in cis.items():
        print(f"    {m}: {c['mean']:.4f} [95% CI: {c['lower']:.4f} - {c['upper']:.4f}]")

process_universe("v2b", r"D:\civix_data\synthetic\profile_v2_v2b")
process_universe("v2c", r"D:\civix_data\synthetic\profile_v2_v2c")

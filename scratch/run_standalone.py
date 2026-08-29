import os
import duckdb
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, f1_score, confusion_matrix
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import time

print("Starting standalone baseline script...", flush=True)
root = Path('D:/civix_data/synthetic/profile_v2_v2a')
feat_path = root / "features_v1/features_merged.parquet"
labs_glob = str(root / "ground_truth/person_labels/*.parquet")
splits_glob = str(root / "ground_truth/train_val_test_split/*.parquet")

def load_data(split):
    con = duckdb.connect(':memory:')
    feat = str(feat_path).replace('\\', '/')
    sql = f"""
    SELECT f.*, l.scenario_class, l.is_positive_label, l.is_false_positive, l.difficulty
    FROM read_parquet('{feat}') f
    JOIN read_parquet('{splits_glob.replace(chr(92), '/')}') s ON s.entity_id = f.person_id
    JOIN read_parquet('{labs_glob.replace(chr(92), '/')}') l ON l.entity_id = f.person_id
    WHERE s.split = '{split}'
    """
    df = con.execute(sql).df()
    con.close()
    
    y = df["is_positive_label"].astype(int)
    scen = df["scenario_class"]
    
    drop_cols = ["person_id", "scenario_class", "is_positive_label", "is_false_positive", "difficulty",
                 "first_call_ts", "last_call_ts", "first_txn_ts", "last_txn_ts"]
    
    # We also need to drop generator artifacts if any exist. Let's just drop non-numeric.
    X = df.drop(columns=[c for c in drop_cols if c in df.columns])
    
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    safe_cat = [c for c in cat_cols if X[c].nunique() < 50]
    high_card = [c for c in cat_cols if c not in safe_cat]
    X = X.drop(columns=high_card)
    if safe_cat:
        X = pd.get_dummies(X, columns=safe_cat, drop_first=True, dtype=float)
    X = X.fillna(0)
    return X, y, scen

print("Loading TRAIN...")
X_train, y_train, scen_train = load_data("TRAIN")
print("Loading TEST...")
X_test, y_test, scen_test = load_data("TEST")

print(f"Train: {X_train.shape}, Test: {X_test.shape}")

# Evaluator
def eval_model(name, model, X, y, scen):
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)[:, 1]
    elif hasattr(model, "decision_function"):
        probs = model.decision_function(X)
    else:
        probs = model.predict(X)

    preds = (probs > 0.5).astype(int)
    roc_auc = roc_auc_score(y, probs)
    precision, recall, _ = precision_recall_curve(y, probs)
    pr_auc = auc(recall, precision)
    f1 = f1_score(y, preds)
    cm = confusion_matrix(y, preds)

    # Top K metrics
    k_1pct = int(len(y) * 0.01)
    k_5pct = int(len(y) * 0.05)
    
    sorted_indices = np.argsort(probs)[::-1]
    y_sorted = y.iloc[sorted_indices].values if isinstance(y, pd.Series) else y[sorted_indices]
    scen_sorted = scen.iloc[sorted_indices].values if isinstance(scen, pd.Series) else scen[sorted_indices]

    def calc_pk_rk(k):
        top_k = y_sorted[:k]
        p_k = top_k.sum() / k
        r_k = top_k.sum() / max(1, y.sum())
        return p_k, r_k

    p_1, r_1 = calc_pk_rk(k_1pct)
    p_5, r_5 = calc_pk_rk(k_5pct)

    print(f"\n--- {name} Results ---")
    print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | F1: {f1:.4f}")
    print(f"P@1%: {p_1:.4f} | R@1%: {r_1:.4f}")
    print(f"P@5%: {p_5:.4f} | R@5%: {r_5:.4f}")
    print(f"Confusion Matrix:\n{cm}")

    is_fp = (scen_sorted[:k_5pct] == 'false_positive')
    print(f"Top 5% alerts that are Hard Negatives (False Positives): {is_fp.sum()} / {k_5pct} ({is_fp.sum()/max(1,k_5pct)*100:.1f}%)")
    total_fps = (scen == 'false_positive').sum()
    print(f"Total False Positives caught in Top 5%: {is_fp.sum()} / {total_fps} ({is_fp.sum()/max(1,total_fps)*100:.1f}%)")

    if hasattr(model, "feature_importances_"):
        fi = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        print("\nTop 10 Features:")
        print(fi.head(10))
    elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("clf"), "coef_"):
        clf = model.named_steps["clf"]
        coef = pd.Series(clf.coef_[0], index=X.columns).abs().sort_values(ascending=False)
        print("\nTop 10 Features (Abs Coef):")
        print(coef.head(10))

# LR
print("\nTraining LR...", flush=True)
lr = Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(class_weight="balanced", max_iter=200))])
lr.fit(X_train, y_train)
eval_model("Logistic Regression", lr, X_test, y_test, scen_test)

# RF
print("\nTraining RF...", flush=True)
rf = RandomForestClassifier(n_estimators=50, max_depth=10, class_weight="balanced", n_jobs=-1)
rf.fit(X_train, y_train)
eval_model("Random Forest", rf, X_test, y_test, scen_test)

# IF
print("\nTraining Isolation Forest...", flush=True)
iso = IsolationForest(n_estimators=50, contamination=0.1, n_jobs=-1)
iso.fit(X_train)
if_preds = iso.predict(X_test)
if_preds_binary = (if_preds == -1).astype(int)
print(f"\n--- Isolation Forest ---")
print(f"Confusion Matrix:\n{confusion_matrix(y_test, if_preds_binary)}")

print("Done.")

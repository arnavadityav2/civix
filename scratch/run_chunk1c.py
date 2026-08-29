import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import time
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.metrics import precision_recall_curve, auc, roc_auc_score, f1_score, confusion_matrix

from civix_ml import config
from civix_ml.features.feature_pipeline import load_training_data
from civix_ml.models.baselines import train_logistic_regression, train_random_forest, train_xgboost
from civix_ml.utils.reproducibility import set_global_seed

# Ensure we're pointing to V2A
config.CIVIX_PROFILE_DIR = Path('D:/civix_data/synthetic/profile_v2_v2a')
config.FEATURES_DIR = config.CIVIX_PROFILE_DIR / "features_v1"
config.LABELS_GLOB = str(config.CIVIX_PROFILE_DIR / "ground_truth" / "person_labels" / "*.parquet")
config.SPLITS_GLOB = str(config.CIVIX_PROFILE_DIR / "ground_truth" / "train_val_test_split" / "*.parquet")
config.MODELS_DIR = Path('D:/civix_data/models/registry/v2')

feature_path = config.FEATURES_DIR / "features_merged.parquet"

print(f"Loading data from {config.CIVIX_PROFILE_DIR}...")
X_train, y_train, scen_train = load_training_data(feature_path, "TRAIN")
X_val, y_val, scen_val = load_training_data(feature_path, "VALIDATION")
X_test, y_test, scen_test = load_training_data(feature_path, "TEST")

print(f"\nTrain: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
print(f"Train Positives: {y_train.sum()}, Val: {y_val.sum()}, Test: {y_test.sum()}")

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

    # Hard Negative evaluation
    # False positive group = scen_class 'false_positive'
    is_fp = (scen_sorted[:k_5pct] == 'false_positive')
    print(f"Top 5% alerts that are Hard Negatives (False Positives): {is_fp.sum()} / {k_5pct} ({is_fp.sum()/k_5pct*100:.1f}%)")

    total_fps = (scen == 'false_positive').sum()
    print(f"Total False Positives caught in Top 5%: {is_fp.sum()} / {total_fps} ({is_fp.sum()/max(1,total_fps)*100:.1f}%)")

    # Feature Importance (if tree)
    if hasattr(model, "feature_importances_"):
        fi = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        print("\nTop 10 Features:")
        print(fi.head(10))
    elif hasattr(model, "named_steps") and hasattr(model.named_steps.get("clf"), "coef_"):
        clf = model.named_steps["clf"]
        coef = pd.Series(clf.coef_[0], index=X.columns).abs().sort_values(ascending=False)
        print("\nTop 10 Features (Abs Coef):")
        print(coef.head(10))

    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "f1": f1,
        "p_1": p_1, "r_1": r_1,
        "p_5": p_5, "r_5": r_5
    }

# LR
lr_model, t_lr = train_logistic_regression(X_train, y_train)
eval_model("Logistic Regression", lr_model, X_test, y_test, scen_test)

# RF
rf_model, t_rf = train_random_forest(X_train, y_train)
eval_model("Random Forest", rf_model, X_test, y_test, scen_test)

from civix_ml.models.baselines import train_isolation_forest

# XGB
try:
    xgb_model, t_xgb = train_xgboost(X_train, y_train, X_val, y_val)
    eval_model("XGBoost", xgb_model, X_test, y_test, scen_test)
except Exception as e:
    print(f"Skipping XGBoost: {e}")

# Isolation Forest
print("\n--- Isolation Forest (Unsupervised) ---")
if_model, t_if = train_isolation_forest(X_train)
# Isolation Forest predicts -1 (anomaly), 1 (normal). We map -1 -> 1 (suspicious)
if_preds = if_model.predict(X_test)
if_preds_binary = (if_preds == -1).astype(int)
cm_if = confusion_matrix(y_test, if_preds_binary)
print(f"Confusion Matrix:\n{cm_if}")
from sklearn.metrics import precision_score, recall_score
print(f"Precision: {precision_score(y_test, if_preds_binary):.4f}")
print(f"Recall: {recall_score(y_test, if_preds_binary):.4f}")

"""
Evaluation metrics for CIVIX Phase 3A.
Focuses on PR-AUC, Precision@K, Recall@K (investigative prioritization metrics).
"""
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_recall_curve, average_precision_score,
    roc_auc_score, f1_score, confusion_matrix,
    precision_score, recall_score, brier_score_loss,
)
from civix_ml.utils import get_logger

log = get_logger(__name__)


def precision_at_k(y_true: np.ndarray, y_scores: np.ndarray, k_pct: float) -> float:
    """Precision@K%: among the top K% ranked entities, what fraction are TP?"""
    k = max(1, int(len(y_true) * k_pct / 100))
    top_k_idx = np.argsort(y_scores)[::-1][:k]
    return y_true[top_k_idx].mean()


def recall_at_k(y_true: np.ndarray, y_scores: np.ndarray, k_pct: float) -> float:
    """Recall@K%: among the top K% ranked entities, what fraction of all positives are caught?"""
    k = max(1, int(len(y_true) * k_pct / 100))
    top_k_idx = np.argsort(y_scores)[::-1][:k]
    total_pos = y_true.sum()
    if total_pos == 0:
        return 0.0
    return y_true[top_k_idx].sum() / total_pos


def evaluate(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    model_name: str = "model",
    threshold: float = 0.5,
) -> dict:
    """
    Compute full evaluation suite.
    Returns dict of metrics suitable for JSON serialization.
    """
    y_pred = (y_scores >= threshold).astype(int)

    pr_auc  = average_precision_score(y_true, y_scores)
    roc_auc = roc_auc_score(y_true, y_scores)
    prec    = precision_score(y_true, y_pred, zero_division=0)
    rec     = recall_score(y_true, y_pred, zero_division=0)
    f1      = f1_score(y_true, y_pred, zero_division=0)
    brier   = brier_score_loss(y_true, y_scores)
    cm      = confusion_matrix(y_true, y_pred).tolist()
    fp_rate = cm[0][1] / max(cm[0][0] + cm[0][1], 1)
    fn_rate = cm[1][0] / max(cm[1][0] + cm[1][1], 1)

    metrics = {
        "model": model_name,
        "pr_auc":    round(pr_auc,  4),
        "roc_auc":   round(roc_auc, 4),
        "precision": round(prec,    4),
        "recall":    round(rec,     4),
        "f1":        round(f1,      4),
        "brier_score": round(brier, 4),
        "false_positive_rate": round(fp_rate, 4),
        "false_negative_rate": round(fn_rate, 4),
        "confusion_matrix": cm,
        "threshold": threshold,
        "n_positives": int(y_true.sum()),
        "n_total":     int(len(y_true)),
    }

    # Precision and Recall at operational thresholds
    for k in [1, 5, 10]:
        metrics[f"precision_at_{k}pct"] = round(precision_at_k(y_true, y_scores, k), 4)
        metrics[f"recall_at_{k}pct"]    = round(recall_at_k(y_true, y_scores, k),    4)

    # Print summary
    log.info(f"  {model_name}: PR-AUC={pr_auc:.4f} | ROC-AUC={roc_auc:.4f} | "
             f"P@1%={metrics['precision_at_1pct']:.3f} | R@1%={metrics['recall_at_1pct']:.3f} | "
             f"F1={f1:.4f}")
    return metrics


def evaluate_isolation_forest(
    y_true: np.ndarray,
    raw_scores: np.ndarray,  # IsolationForest.score_samples() (lower = more anomalous)
    model_name: str = "IsolationForest",
) -> dict:
    """
    IsolationForest outputs raw_scores where LOWER = more anomalous.
    Negate to get anomaly_score where HIGHER = more anomalous.
    """
    anomaly_scores = -raw_scores  # flip sign so higher = more suspicious
    return evaluate(y_true, anomaly_scores, model_name=model_name)

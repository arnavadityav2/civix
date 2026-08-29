"""Adversarial evaluation — tests hard-negative discrimination."""
import numpy as np
import pandas as pd
from civix_ml.evaluation.metrics import evaluate, precision_at_k, recall_at_k
from civix_ml.utils import get_logger

log = get_logger(__name__)


def run_adversarial_tests(
    X_test: pd.DataFrame,
    y_true: pd.Series,
    y_scenario: pd.Series,
    y_fp: pd.Series,
    model,
    model_name: str,
    feature_names: list[str],
) -> dict:
    """
    Run adversarial sub-group evaluations.
    Returns dict of per-group metrics.
    """
    results = {}

    # Get prediction scores
    if hasattr(model, "predict_proba"):
        scores = model.predict_proba(X_test)[:, 1]
    elif hasattr(model, "score_samples"):
        scores = -model.score_samples(X_test)
    else:
        scores = model.decision_function(X_test)
    scores = np.array(scores)
    y_arr = np.array(y_true)
    y_sc  = np.array(y_scenario)
    y_fp_arr = np.array(y_fp)

    # A — Overall test metrics
    results["overall"] = evaluate(y_arr, scores, model_name=model_name)

    # B — False Positive subset: should NOT be flagged by model
    fp_mask = y_fp_arr == True
    if fp_mask.sum() > 0:
        fp_scores = scores[fp_mask]
        fp_y      = y_arr[fp_mask]
        # For false positives (label=0), good model gives low scores
        fp_flagged_rate = (fp_scores >= 0.5).mean()
        results["false_positive_flag_rate"] = round(float(fp_flagged_rate), 4)
        results["false_positive_avg_score"] = round(float(fp_scores.mean()), 4)
        log.info(f"  [Adversarial] False-positive group: avg_score={fp_scores.mean():.3f}, "
                 f"flagged_rate={fp_flagged_rate:.3f} (should be LOW)")

    # C — High-volume persons: top 10% by total_calls
    if "total_calls" in X_test.columns:
        call_thresh = X_test["total_calls"].quantile(0.90)
        hv_mask = X_test["total_calls"] >= call_thresh
        hv_y = y_arr[hv_mask]
        hv_scores = scores[hv_mask]
        if len(hv_y) > 0:
            hv_fp_rate = ((hv_scores >= 0.5) & (hv_y == 0)).sum() / max((hv_y == 0).sum(), 1)
            results["high_call_volume_fp_rate"] = round(float(hv_fp_rate), 4)
            log.info(f"  [Adversarial] High-call-volume (top 10%): FP rate={hv_fp_rate:.3f}")

    # D — High-transaction persons: top 10% by total_txns
    if "total_txns" in X_test.columns:
        txn_thresh = X_test["total_txns"].quantile(0.90)
        ht_mask = X_test["total_txns"] >= txn_thresh
        ht_y = y_arr[ht_mask]
        ht_scores = scores[ht_mask]
        if len(ht_y) > 0:
            ht_fp_rate = ((ht_scores >= 0.5) & (ht_y == 0)).sum() / max((ht_y == 0).sum(), 1)
            results["high_txn_volume_fp_rate"] = round(float(ht_fp_rate), 4)
            log.info(f"  [Adversarial] High-txn-volume (top 10%): FP rate={ht_fp_rate:.3f}")

    # E — Sparse profiles: bottom 10% by total_calls (low-data entities)
    if "total_calls" in X_test.columns:
        sparse_thresh = X_test["total_calls"].quantile(0.10)
        sp_mask = X_test["total_calls"] <= sparse_thresh
        sp_y = y_arr[sp_mask]
        sp_scores = scores[sp_mask]
        if sp_y.sum() > 0:
            sp_recall = recall_at_k(sp_y, sp_scores, 10)
            results["sparse_profile_recall_at_10pct"] = round(float(sp_recall), 4)
            log.info(f"  [Adversarial] Sparse profiles: recall@10%={sp_recall:.3f}")

    # F — Confirmed pattern by difficulty
    for difficulty in ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]:
        diff_mask = (y_sc == "confirmed_pattern")
        # We don't have difficulty in X — report by scenario
        if diff_mask.sum() > 0:
            diff_prec = precision_at_k(y_arr[diff_mask], scores[diff_mask], 50)
            results[f"confirmed_precision_at_50pct"] = round(float(diff_prec), 4)
            break

    return results

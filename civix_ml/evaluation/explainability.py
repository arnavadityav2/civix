"""
CIVIX Graph Explainability — Phase 3B
Produces human-readable, investigator-appropriate explanations for high-risk nodes.
CRITICAL: Outputs are risk signals, NOT proof of criminality.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from civix_ml.utils import get_logger

log = get_logger(__name__)

# Thresholds for "unusual" flags (percentile-based — set at training time)
PERCENTILE_HIGH = 90   # top 10%
PERCENTILE_VERY_HIGH = 99   # top 1%


def explain_person(
    person_id: str,
    beh_features: dict,
    graph_features: dict,
    model_score: float,
    population_percentiles: dict,
) -> dict:
    """
    Generate a structured, investigator-readable explanation for a scored person.

    Returns a dict with:
    - risk_score: float (model output probability)
    - risk_signals: list of human-readable signals
    - evidence: dict of key metrics with context
    - disclaimer: mandatory legal/ethical disclaimer
    """
    signals = []
    evidence = {}

    # ── Communication graph signals ───────────────────────────────────────────
    out_deg = graph_features.get("cdr_out_degree", 0)
    if out_deg is not None and population_percentiles.get("cdr_out_degree_p90"):
        if out_deg >= population_percentiles["cdr_out_degree_p99"]:
            signals.append("Exceptionally high communication network breadth (top 1% of population)")
        elif out_deg >= population_percentiles["cdr_out_degree_p90"]:
            signals.append("Elevated communication network breadth (top 10% of population)")
        evidence["communication_pairs"] = {"value": out_deg, "unit": "unique phone pair relationships"}

    recip = graph_features.get("cdr_reciprocity_ratio", None)
    if recip is not None:
        if recip < 0.1:
            signals.append("Very low communication reciprocity — predominantly outgoing contact pattern")
        evidence["reciprocity_ratio"] = {"value": round(recip, 3), "unit": "fraction of reciprocal pairs"}

    conc = graph_features.get("cdr_call_concentration", None)
    if conc is not None:
        if conc >= 0.5:
            signals.append("High call volume concentration on single contact")
        evidence["call_concentration"] = {"value": round(conc, 3), "unit": "fraction of calls to top contact"}

    # ── Financial graph signals ───────────────────────────────────────────────
    txn_deg = graph_features.get("txn_total_degree", 0)
    if txn_deg and population_percentiles.get("txn_total_degree_p90"):
        if txn_deg >= population_percentiles["txn_total_degree_p99"]:
            signals.append("Exceptionally high financial network connectivity (top 1%)")
        evidence["financial_network_size"] = {"value": txn_deg, "unit": "account relationships"}

    flow_ratio = graph_features.get("txn_net_flow_ratio", None)
    if flow_ratio is not None:
        if flow_ratio > 0.9:
            signals.append("Predominantly outbound financial flow — entity is a net sender")
        elif flow_ratio < 0.1:
            signals.append("Predominantly inbound financial flow — entity is a net receiver")
        evidence["net_flow_ratio"] = {"value": round(flow_ratio, 3), "unit": "fraction outbound"}

    # ── PageRank signal ───────────────────────────────────────────────────────
    pr = graph_features.get("cdr_pagerank_approx", None)
    if pr is not None and population_percentiles.get("cdr_pagerank_approx_p90"):
        if pr >= population_percentiles["cdr_pagerank_approx_p99"]:
            signals.append("Network centrality is in the top 1% — entity is a network hub")
        evidence["network_centrality_approx"] = {"value": round(pr, 4), "unit": "degree-weighted PageRank approx"}

    # ── Behavioral signals ───────────────────────────────────────────────────
    high_val = beh_features.get("high_value_txn_count", 0)
    if high_val and high_val > 5:
        signals.append(f"Multiple high-value transactions detected ({int(high_val)} events)")
        evidence["high_value_transactions"] = {"value": int(high_val), "unit": "count"}

    night_ratio = beh_features.get("night_call_ratio", 0)
    if night_ratio and night_ratio > 0.2:
        signals.append(f"Elevated night-time communication activity ({night_ratio:.0%} of calls)")
        evidence["night_call_ratio"] = {"value": round(night_ratio, 3), "unit": "fraction at night"}

    return {
        "person_id":      person_id,
        "risk_score":     round(model_score, 4),
        "risk_signals":   signals if signals else ["No specific anomalous signals identified"],
        "evidence":       evidence,
        "signal_count":   len(signals),
        "disclaimer": (
            "This output represents a model-derived investigative risk signal based on "
            "behavioral and network pattern analysis. It does NOT constitute evidence of "
            "criminal activity, guilt, or any legal finding. All alerts must be reviewed "
            "by a qualified human investigator before any action is taken. CIVIX is a "
            "decision-support tool, not an automated judgment system."
        ),
    }


def explain_batch(
    person_ids:          list[str],
    beh_feature_rows:    list[dict],
    graph_feature_rows:  list[dict],
    model_scores:        list[float],
    graph_df:            pd.DataFrame,   # for computing population percentiles
) -> list[dict]:
    """Explain a batch of persons."""
    # Compute population percentiles for context
    num_cols = [c for c in graph_df.columns if c != "person_id" and graph_df[c].dtype in [float, int]]
    percentiles = {}
    for col in num_cols:
        percentiles[f"{col}_p90"] = float(np.percentile(graph_df[col].fillna(0), 90))
        percentiles[f"{col}_p99"] = float(np.percentile(graph_df[col].fillna(0), 99))

    results = []
    for pid, beh, grph, score in zip(person_ids, beh_feature_rows, graph_feature_rows, model_scores):
        results.append(explain_person(pid, beh, grph, score, percentiles))
    return results

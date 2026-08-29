"""
CIVIX Synthetic World V2: Ground Truth Labels
civix_generator/v2/ground_truth.py

Derives labels from the HIDDEN WORLD STATE, not from observable features.

Label derivation rules:
1. confirmed_pattern: person is a member of a criminal network community
   (assigned during adversarial_engine → community → scenario_engine)
2. false_positive: person has a suspicious behavioral profile BUT is NOT
   a criminal network member (hard negatives from adversarial_engine)
3. suspicious: person has some elevated behavioral traits but is not
   definitively a criminal network member
4. normal: no criminal network membership, no elevated behavioral red flags

The key invariant:
    label = f(hidden_world_state) ≠ f(observed_features)

Some confirmed_pattern persons are behaviorally quiet (low-visibility).
Some normal persons are behaviorally loud (hard negatives).
The label is correct even when the features are misleading.
"""
from __future__ import annotations
from typing import Any, Dict, Iterator, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank


def generate_person_labels(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    community_catalog: Dict[int, Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Yield ground-truth label records for each person.

    These records must ONLY be written to the ground_truth/ Parquet shard.
    They must NEVER appear in the observable feature data.
    """
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    # Build person → criminal_community membership map
    person_in_criminal_comm: set[int] = set()
    for cid, meta in community_catalog.items():
        if meta.get("is_criminal", False):
            for m in meta["members"]:
                person_in_criminal_comm.add(m)

    for pop in population:
        sc     = pop["scenario_class"]
        idx    = pop["person_index"]
        is_lv  = bool(pop.get("_low_visibility", False))
        is_hn  = bool(pop.get("_hard_negative", False))
        is_bridge = idx in person_in_criminal_comm and sc == "normal"

        # ── Derive label ──────────────────────────────────────────────────────
        if sc == "confirmed_pattern":
            is_positive  = True
            is_fp        = False
        elif sc == "false_positive":
            is_positive  = False
            is_fp        = True
        elif sc == "suspicious":
            is_positive  = False
            is_fp        = False
        else:  # normal (including hard negatives and bridge nodes)
            is_positive  = False
            is_fp        = is_hn != "" and is_hn is not False   # bridge nodes look FP-like

        # ── Risk score: derived from world state, not features ─────────────
        # This is the TRUE risk score from the hidden world.
        # MUST NOT be exposed in feature columns.
        if sc == "confirmed_pattern" and is_lv:
            risk_gt = round(float(0.65 + 0.25 * (1 - pop.get("_risk_exposure", 0.5))), 3)
        elif sc == "confirmed_pattern":
            risk_gt = round(float(0.70 + 0.28 * pop.get("_risk_exposure", 0.7)), 3)
        elif sc == "suspicious":
            risk_gt = round(float(0.30 + 0.40 * pop.get("_risk_exposure", 0.5)), 3)
        elif sc == "false_positive":
            risk_gt = round(float(0.05 + 0.30 * pop.get("_risk_exposure", 0.3)), 3)
        else:
            risk_gt = round(float(0.01 + 0.20 * pop.get("_risk_exposure", 0.1)), 3)

        risk_gt = min(0.99, max(0.01, risk_gt))

        family   = pop.get("scenario_family", "unknown")
        category = pop.get("scenario_category", "unknown")
        diff     = pop.get("difficulty", "LOW")

        batch.append({
            "entity_id":         pop["person_id"],
            "entity_type":       "person",
            "person_index":      idx,
            "scenario_class":    sc,
            "scenario_family":   family,
            "scenario_category": category,
            "difficulty":        diff,
            "is_positive_label": bool(is_positive),
            "is_false_positive": bool(is_fp),
            "is_low_visibility": is_lv,
            "is_hard_negative":  (pop.get("_hard_negative") or "") != "",
            "is_bridge_node":    is_bridge,
            "in_criminal_network": idx in person_in_criminal_comm,
            "risk_score_gt":     risk_gt,
            "ground_truth_note": f"{sc} / {family}",
        })

        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_train_val_test_split(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
) -> Iterator[List[Dict[str, Any]]]:
    """
    Assign temporal train/validation/test splits.

    Split strategy:
    - TRAIN:      active_start_day < train_cutoff_day
    - VALIDATION: train_cutoff_day ≤ active_start_day < val_cutoff_day
    - TEST:       active_start_day ≥ val_cutoff_day

    Fallback to stratified index-based split if any split is empty.
    """
    train_cut = config.train_cutoff_day
    val_cut   = config.val_cutoff_day
    n         = len(population)

    # Count temporal assignments first
    splits = {}
    counts = {"TRAIN": 0, "VALIDATION": 0, "TEST": 0}
    for pop in population:
        sd = pop["active_start_day"]
        if sd < train_cut:
            splits[pop["person_index"]] = "TRAIN"
            counts["TRAIN"] += 1
        elif sd < val_cut:
            splits[pop["person_index"]] = "VALIDATION"
            counts["VALIDATION"] += 1
        else:
            splits[pop["person_index"]] = "TEST"
            counts["TEST"] += 1

    use_stratified = any(v == 0 for v in counts.values())

    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    for pop in population:
        idx = pop["person_index"]
        if use_stratified:
            if idx < int(n * 0.70):
                split = "TRAIN"
            elif idx < int(n * 0.85):
                split = "VALIDATION"
            else:
                split = "TEST"
        else:
            split = splits[idx]

        batch.append({
            "entity_id":        pop["person_id"],
            "person_index":     idx,
            "split":            split,
            "active_start_day": pop["active_start_day"],
            "scenario_class":   pop["scenario_class"],
        })

        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch

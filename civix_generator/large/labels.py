"""
CIVIX Large-Scale Generator: Ground Truth Labels (SEPARATE from features)
civix_generator/large/labels.py

Produces the label/ground-truth Parquet files.
These MUST NEVER be mixed into the feature columns.
"""
from __future__ import annotations
from typing import Iterator, List, Dict, Any

from .seeds import make_uuid
from .config import ProfileConfig

# Label schema
# ─────────────────────────────────────────────────────────────────────────────
# entity_id        UUID of person/account/etc.
# entity_type      "person" | "account" | "transaction" | "case" | "cdr"
# scenario_class   "normal" | "suspicious" | "confirmed_pattern" | "false_positive"
# scenario_family  e.g. "structuring", "geo_anomaly", "corruption_cycle"
# scenario_id_str  e.g. "FIN-04"
# scenario_category  "telecom" | "financial" | "property" | "crime" | "adversarial" | "identity"
# difficulty       "LOW" | "MEDIUM" | "HIGH" | "VERY_HIGH"
# is_positive_label  True if this entity/event is an investigative target
# is_false_positive  True if this entity LOOKS suspicious but is innocent
# ground_truth_note  Human-readable description (for debugging only)
# ─────────────────────────────────────────────────────────────────────────────


def generate_person_labels(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
) -> Iterator[List[Dict[str, Any]]]:
    """Yield ground-truth labels for each person."""
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    for pop in population:
        sc_class  = pop["scenario_class"]
        is_pos    = sc_class == "confirmed_pattern"
        is_fp     = sc_class == "false_positive"

        batch.append({
            "entity_id":          pop["person_id"],
            "entity_type":        "person",
            "person_index":       pop["person_index"],
            "scenario_class":     sc_class,
            "scenario_family":    pop["scenario_family"],
            "scenario_id_str":    pop["scenario_id_str"],
            "scenario_category":  pop["scenario_category"],
            "difficulty":         pop["difficulty"],
            "is_positive_label":  is_pos,
            "is_false_positive":  is_fp,
            "risk_score_gt":      pop["risk_score"],
            "ground_truth_note":  f"{pop['scenario_family']} scenario",
        })

        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_train_val_test_split(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
) -> Iterator[List[Dict[str, Any]]]:
    """Assign each person to TRAIN / VAL / TEST.

    Strategy:
    - Primary: temporal split on active_start_day (prevents leakage).
    - Fallback: if a split gets 0 persons (short profiles where all persons
      start early), fall back to stratified index-based assignment.
    """
    total_days = config.total_days
    train_cutoff = int(total_days * 0.70)
    val_cutoff   = int(total_days * 0.85)

    # First pass: temporal assignment
    temporal = {}
    for pop in population:
        start_day = pop["active_start_day"]
        if start_day < train_cutoff:
            temporal[pop["person_index"]] = "TRAIN"
        elif start_day < val_cutoff:
            temporal[pop["person_index"]] = "VALIDATION"
        else:
            temporal[pop["person_index"]] = "TEST"

    counts = {"TRAIN": 0, "VALIDATION": 0, "TEST": 0}
    for v in temporal.values():
        counts[v] += 1

    # If any split is empty, override with stratified split on index
    use_stratified = any(v == 0 for v in counts.values())
    n = len(population)

    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    for pop in population:
        idx = pop["person_index"]
        if use_stratified:
            # Deterministic index-based: 70/15/15
            if idx < int(n * 0.70):
                split = "TRAIN"
            elif idx < int(n * 0.85):
                split = "VALIDATION"
            else:
                split = "TEST"
        else:
            split = temporal[idx]

        batch.append({
            "entity_id":        pop["person_id"],
            "person_index":     pop["person_index"],
            "split":            split,
            "active_start_day": pop["active_start_day"],
        })

        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch

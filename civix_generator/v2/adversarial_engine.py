"""
CIVIX Synthetic World V2: Adversarial Engine
civix_generator/v2/adversarial_engine.py

Applies post-population-assignment modifications to inject:

1. HARD NEGATIVES: Normal persons with behaviors that overlap suspicious profiles
   - High-volume legitimate users (call centers, sales)
   - High-mobility legitimate users (truck drivers, sales reps)
   - High-finance legitimate users (business owners, traders)
   - Phone churn (legitimate phone replacement)
   - Network hubs (popular persons)
   - Burst activity windows (event organizers, festival season)

2. LOW-VISIBILITY CRIMINALS: Confirmed_pattern persons who are behaviorally quiet
   - Low communication_activity (fewer calls than average normal person)
   - Single stable device
   - Low transaction volume
   - Geographically static
   - Suspicious only from network position

3. SCENARIO FAMILY DIVERSITY: Ensures confirmed_pattern contains all required
   pathway types (coordinated_comm, financial_layering, burner_rotation,
   geo_coordination, hub_spoke, chain, ring, low_visibility, bridge, mixed)

All modifications are applied IN-PLACE to the population list.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, List

from .config import V2ProfileConfig, AdversarialParams
from .seeds import V2SeedBank

# All required pathway families for scenario diversity requirement
REQUIRED_PATHWAYS = [
    "coordinated_comm",
    "financial_layering",
    "burner_rotation",
    "geo_coordination",
    "hub_spoke",
    "chain",
    "ring",
    "low_visibility",
    "bridge",
    "mixed_comm_fin",
]


def apply_adversarial_modifications(
    population: List[Dict[str, Any]],
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> None:
    """
    Apply all adversarial modifications in-place.
    This must be called AFTER assign_population() and BEFORE CDR generation.
    """
    rng = seed_bank.get("adversarial")
    ap  = config.adversarial_params

    # Index by scenario
    normal_idx    = [p["person_index"] for p in population if p["scenario_class"] == "normal"]
    confirmed_idx = [p["person_index"] for p in population if p["scenario_class"] == "confirmed_pattern"]
    fp_idx        = [p["person_index"] for p in population if p["scenario_class"] == "false_positive"]

    # ── 1. HARD NEGATIVES ─────────────────────────────────────────────────────
    n_normal = len(normal_idx)
    rng_hn   = seed_bank.get("hard_negative")

    # 1a. High-volume (call-center / sales)
    n_hv = max(1, int(n_normal * ap.high_volume_legitimate_rate))
    hv_pool = rng_hn.choice(normal_idx, size=min(n_hv, n_normal), replace=False)
    for idx in hv_pool:
        p = population[idx]
        p["_comm_activity"]  = float(np.clip(p["_comm_activity"] * rng_hn.uniform(1.8, 3.5), 0.01, 0.99))
        p["_occupation"]     = "business"
        p["_is_business"]    = True
        p["_hard_negative"]  = "high_volume_legitimate"

    # 1b. High-mobility (traveler)
    n_mob = max(1, int(n_normal * ap.high_mobility_legitimate_rate))
    mob_pool = rng_hn.choice(normal_idx, size=min(n_mob, n_normal), replace=False)
    for idx in mob_pool:
        p = population[idx]
        p["_mobility"]       = float(np.clip(rng_hn.uniform(0.7, 0.95), 0.01, 0.99))
        p["_hard_negative"]  = "high_mobility_legitimate"

    # 1c. High-finance (business owner / trader)
    n_fin = max(1, int(n_normal * ap.high_finance_legitimate_rate))
    fin_pool = rng_hn.choice(normal_idx, size=min(n_fin, n_normal), replace=False)
    for idx in fin_pool:
        p = population[idx]
        p["_fin_activity"]   = float(np.clip(rng_hn.uniform(0.6, 0.95), 0.01, 0.99))
        p["_income_band"]    = int(rng_hn.choice([3, 4]))
        p["_is_business"]    = True
        p["_hard_negative"]  = "high_finance_legitimate"

    # 1d. Phone churners (legitimate)
    n_churn = max(1, int(n_normal * ap.phone_churn_legitimate_rate))
    ch_pool = rng_hn.choice(normal_idx, size=min(n_churn, n_normal), replace=False)
    for idx in ch_pool:
        p = population[idx]
        p["_phone_churn"]    = float(np.clip(rng_hn.uniform(0.6, 0.90), 0.01, 0.99))
        p["_device_stability"] = float(np.clip(rng_hn.uniform(0.1, 0.35), 0.01, 0.99))
        p["_hard_negative"]  = "phone_churn_legitimate"

    # 1e. Network hubs (popular persons)
    n_hub = max(1, int(n_normal * ap.high_centrality_legitimate_rate))
    hub_pool = rng_hn.choice(normal_idx, size=min(n_hub, n_normal), replace=False)
    for idx in hub_pool:
        p = population[idx]
        p["_centrality_tendency"] = float(np.clip(rng_hn.uniform(0.7, 0.95), 0.01, 0.99))
        p["_social"]              = float(np.clip(rng_hn.uniform(0.7, 0.95), 0.01, 0.99))
        p["_hard_negative"]       = "high_centrality_legitimate"

    # 1f. Burst activity (event organizers, festival season)
    n_burst = max(1, int(n_normal * ap.burst_activity_legitimate_rate))
    burst_pool = rng_hn.choice(normal_idx, size=min(n_burst, n_normal), replace=False)
    for idx in burst_pool:
        p = population[idx]
        p["_burst_active"]   = True
        p["_hard_negative"]  = "burst_activity_legitimate"

    # ── 2. LOW-VISIBILITY CRIMINALS ────────────────────────────────────────────
    rng_lv = seed_bank.get("adversarial")
    n_lv   = max(1, int(len(confirmed_idx) * ap.low_visibility_criminal_rate))
    lv_pool = rng_lv.choice(confirmed_idx, size=min(n_lv, len(confirmed_idx)), replace=False)
    for idx in lv_pool:
        p = population[idx]
        p["_comm_activity"]    = float(np.clip(rng_lv.uniform(0.05, 0.25), 0.01, 0.99))
        p["_fin_activity"]     = float(np.clip(rng_lv.uniform(0.05, 0.20), 0.01, 0.99))
        p["_device_stability"] = float(np.clip(rng_lv.uniform(0.75, 0.99), 0.01, 0.99))
        p["_phone_churn"]      = float(np.clip(rng_lv.uniform(0.01, 0.10), 0.01, 0.99))
        p["_mobility"]         = float(np.clip(rng_lv.uniform(0.05, 0.25), 0.01, 0.99))
        p["_low_visibility"]   = True

    # ── 3. SCENARIO FAMILY DIVERSITY ──────────────────────────────────────────
    # Distribute confirmed_pattern persons across all required pathways
    # Also assign some suspicious persons to pathway families
    _assign_pathway_diversity(population, confirmed_idx, "confirmed_pattern", rng, config)
    suspicious_idx = [p["person_index"] for p in population if p["scenario_class"] == "suspicious"]
    _assign_pathway_diversity(population, suspicious_idx, "suspicious", rng, config)


def _assign_pathway_diversity(
    population: List[Dict[str, Any]],
    target_idxs: List[int],
    sc_class: str,
    rng: np.random.Generator,
    config: V2ProfileConfig,
) -> None:
    """
    Distribute persons across pathway families ensuring all REQUIRED_PATHWAYS
    are covered. Uses round-robin + random assignment.
    """
    if not target_idxs:
        return

    n = len(target_idxs)
    shuffled = list(rng.permutation(target_idxs))

    for i, idx in enumerate(shuffled):
        # Primary pathway (round-robin across required)
        pathway = REQUIRED_PATHWAYS[i % len(REQUIRED_PATHWAYS)]
        population[idx]["scenario_family"]   = pathway
        population[idx]["scenario_category"] = _pathway_to_category(pathway)
        population[idx]["difficulty"]        = _pathway_to_difficulty(pathway, rng)

        # A person can have a secondary pathway (mixed behavior)
        if rng.random() < 0.15:
            secondary = REQUIRED_PATHWAYS[rng.integers(0, len(REQUIRED_PATHWAYS))]
            population[idx]["scenario_family_secondary"] = secondary


def _pathway_to_category(pathway: str) -> str:
    mapping = {
        "coordinated_comm":   "telecom",
        "financial_layering": "financial",
        "burner_rotation":    "telecom",
        "geo_coordination":   "geographic",
        "hub_spoke":          "network",
        "chain":              "network",
        "ring":               "network",
        "low_visibility":     "network",
        "bridge":             "network",
        "mixed_comm_fin":     "combined",
    }
    return mapping.get(pathway, "unknown")


def _pathway_to_difficulty(pathway: str, rng: np.random.Generator) -> str:
    """
    Low-visibility and bridge nodes are hardest.
    Coordinated communication hubs are medium (behaviorally obvious).
    """
    hard = {"low_visibility", "bridge", "financial_layering", "geo_coordination"}
    medium = {"chain", "ring", "mixed_comm_fin"}
    if pathway in hard:
        return str(rng.choice(["HIGH", "VERY_HIGH"], p=[0.5, 0.5]))
    elif pathway in medium:
        return str(rng.choice(["MEDIUM", "HIGH"], p=[0.6, 0.4]))
    else:
        return str(rng.choice(["LOW", "MEDIUM"], p=[0.5, 0.5]))

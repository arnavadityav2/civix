"""
CIVIX Large-Scale Generator: Scenario Engine
civix_generator/large/scenarios.py

Assigns every generated person a scenario class and family.
The scenario assignment table (the ground-truth label) is kept
completely separate from the observable feature data.

Scenario assignment is deterministic per (seed, person_index).
"""
from __future__ import annotations
import random
import hashlib
from typing import Dict, Any, List, Optional
import numpy as np

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig, ScenarioDist

# ─── Scenario families catalogue ─────────────────────────────────────────────
# Each entry: (scenario_type, category, difficulty, default_weight)
SCENARIO_REGISTRY: List[Dict[str, Any]] = [
    # IDENTITY (IDENT-01 to IDENT-08)
    {"id": "IDENT-01", "type": "genuine_identity",       "category": "identity",   "difficulty": "LOW",      "class": "normal"},
    {"id": "IDENT-02", "type": "duplicate_identity",     "category": "identity",   "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "IDENT-03", "type": "alias_innocent",         "category": "identity",   "difficulty": "MEDIUM",   "class": "false_positive"},
    {"id": "IDENT-04", "type": "alias_criminal",         "category": "identity",   "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "IDENT-05", "type": "spelling_variation",     "category": "identity",   "difficulty": "MEDIUM",   "class": "normal"},
    {"id": "IDENT-06", "type": "identity_collision",     "category": "identity",   "difficulty": "VERY_HIGH","class": "suspicious"},
    {"id": "IDENT-07", "type": "deceased_reuse",         "category": "identity",   "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "IDENT-08", "type": "shared_indicators",      "category": "identity",   "difficulty": "MEDIUM",   "class": "false_positive"},
    # TELECOM (TEL-01 to TEL-12)
    {"id": "TEL-01",   "type": "normal_caller",          "category": "telecom",    "difficulty": "LOW",      "class": "normal"},
    {"id": "TEL-02",   "type": "high_freq_innocent",     "category": "telecom",    "difficulty": "HIGH",     "class": "false_positive"},
    {"id": "TEL-03",   "type": "burner_sim",             "category": "telecom",    "difficulty": "MEDIUM",   "class": "suspicious"},
    {"id": "TEL-04",   "type": "sim_reassignment",       "category": "telecom",    "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "TEL-05",   "type": "shared_device_family",   "category": "telecom",    "difficulty": "HIGH",     "class": "false_positive"},
    {"id": "TEL-06",   "type": "shared_sim_criminal",    "category": "telecom",    "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "TEL-07",   "type": "device_reassignment",    "category": "telecom",    "difficulty": "MEDIUM",   "class": "normal"},
    {"id": "TEL-08",   "type": "cross_region_travel",    "category": "telecom",    "difficulty": "MEDIUM",   "class": "normal"},
    {"id": "TEL-09",   "type": "geo_anomaly",            "category": "telecom",    "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "TEL-10",   "type": "silent_then_burst",      "category": "telecom",    "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "TEL-11",   "type": "coordinated_comm",       "category": "telecom",    "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "TEL-12",   "type": "tower_hopping",          "category": "telecom",    "difficulty": "HIGH",     "class": "suspicious"},
    # FINANCIAL (FIN-01 to FIN-14)
    {"id": "FIN-01",   "type": "salary_pattern",         "category": "financial",  "difficulty": "LOW",      "class": "normal"},
    {"id": "FIN-02",   "type": "recurring_bills",        "category": "financial",  "difficulty": "LOW",      "class": "normal"},
    {"id": "FIN-03",   "type": "high_value_legit",       "category": "financial",  "difficulty": "HIGH",     "class": "false_positive"},
    {"id": "FIN-04",   "type": "structuring",            "category": "financial",  "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "FIN-05",   "type": "transaction_burst",      "category": "financial",  "difficulty": "MEDIUM",   "class": "suspicious"},
    {"id": "FIN-06",   "type": "circular_transactions",  "category": "financial",  "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "FIN-07",   "type": "mule_account",           "category": "financial",  "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "FIN-08",   "type": "joint_account_legit",    "category": "financial",  "difficulty": "LOW",      "class": "normal"},
    {"id": "FIN-09",   "type": "authorized_signatory",   "category": "financial",  "difficulty": "MEDIUM",   "class": "normal"},
    {"id": "FIN-10",   "type": "proxy_transaction",      "category": "financial",  "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "FIN-11",   "type": "dormant_reactivation",   "category": "financial",  "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "FIN-12",   "type": "rapid_fund_movement",    "category": "financial",  "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "FIN-13",   "type": "geo_txn_anomaly",        "category": "financial",  "difficulty": "MEDIUM",   "class": "suspicious"},
    {"id": "FIN-14",   "type": "corruption_cycle",       "category": "financial",  "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    # PROPERTY (PROP-01 to PROP-09)
    {"id": "PROP-01",  "type": "normal_transfer",        "category": "property",   "difficulty": "LOW",      "class": "normal"},
    {"id": "PROP-02",  "type": "repeated_ownership",     "category": "property",   "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "PROP-03",  "type": "suspicious_transfer",    "category": "property",   "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "PROP-04",  "type": "rapid_resale",           "category": "property",   "difficulty": "MEDIUM",   "class": "suspicious"},
    {"id": "PROP-05",  "type": "proxy_ownership",        "category": "property",   "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "PROP-06",  "type": "adjacent_mutation",      "category": "property",   "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "PROP-07",  "type": "multi_case_property",    "category": "property",   "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "PROP-08",  "type": "inconsistent_registry",  "category": "property",   "difficulty": "VERY_HIGH","class": "suspicious"},
    {"id": "PROP-09",  "type": "benami_property",        "category": "property",   "difficulty": "HIGH",     "class": "confirmed_pattern"},
    # CRIME (CRIME-01 to CRIME-18)
    {"id": "CRIME-01", "type": "theft",                  "category": "crime",      "difficulty": "LOW",      "class": "confirmed_pattern"},
    {"id": "CRIME-02", "type": "robbery",                "category": "crime",      "difficulty": "MEDIUM",   "class": "confirmed_pattern"},
    {"id": "CRIME-03", "type": "burglary",               "category": "crime",      "difficulty": "MEDIUM",   "class": "confirmed_pattern"},
    {"id": "CRIME-04", "type": "fraud",                  "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-05", "type": "cyber_fraud",            "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-06", "type": "organized_financial",    "category": "crime",      "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "CRIME-07", "type": "kidnapping",             "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-08", "type": "missing_person",         "category": "crime",      "difficulty": "MEDIUM",   "class": "suspicious"},
    {"id": "CRIME-09", "type": "assault",                "category": "crime",      "difficulty": "LOW",      "class": "confirmed_pattern"},
    {"id": "CRIME-10", "type": "organized_crime",        "category": "crime",      "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "CRIME-11", "type": "trafficking",            "category": "crime",      "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "CRIME-12", "type": "extortion",              "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-13", "type": "illegal_property",       "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-14", "type": "vehicle_crime",          "category": "crime",      "difficulty": "MEDIUM",   "class": "confirmed_pattern"},
    {"id": "CRIME-15", "type": "identity_fraud",         "category": "crime",      "difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "CRIME-16", "type": "suspicious_death",       "category": "crime",      "difficulty": "HIGH",     "class": "suspicious"},
    {"id": "CRIME-17", "type": "gang_activity",          "category": "crime",      "difficulty": "HIGH",     "class": "confirmed_pattern"},
    {"id": "CRIME-18", "type": "repeat_offender",        "category": "crime",      "difficulty": "MEDIUM",   "class": "confirmed_pattern"},
    # ADVERSARIAL (ADV-01 to ADV-25)
    {"id": "ADV-01",   "type": "identity_collision_adv", "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
    {"id": "ADV-02",   "type": "sim_reassignment_adv",   "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
    {"id": "ADV-05",   "type": "false_positive_network", "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
    {"id": "ADV-06",   "type": "innocent_high_freq",     "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
    {"id": "ADV-11",   "type": "multi_hop_hidden",       "category": "adversarial","difficulty": "VERY_HIGH","class": "confirmed_pattern"},
    {"id": "ADV-14",   "type": "coordinated_finance_innocent","category":"adversarial","difficulty":"VERY_HIGH","class":"false_positive"},
    {"id": "ADV-15",   "type": "geo_anomaly_innocent",   "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
    {"id": "ADV-16",   "type": "decoy_suspect",          "category": "adversarial","difficulty": "VERY_HIGH","class": "false_positive"},
]

# ─── Per-class scenario selection pools ──────────────────────────────────────
_BY_CLASS: Dict[str, List[Dict]] = {}
for s in SCENARIO_REGISTRY:
    _BY_CLASS.setdefault(s["class"], []).append(s)

# Activity-level profiles (CDRs per person, rough range)
ACTIVITY_PROFILES = {
    "normal":            (50,  600),
    "suspicious":        (100, 1200),
    "confirmed_pattern": (200, 2000),
    "false_positive":    (200, 2000),
}


class RoleResolver:
    def __init__(self, config: ProfileConfig):
        self.config = config
        self.role_to_index: Dict[str, int] = {}
        self.reserved_indices = set()
        
    def resolve(self, scenario_id: str, role_id: str) -> int:
        if role_id in self.role_to_index:
            return self.role_to_index[role_id]
            
        key = f"{self.config.seed}|{scenario_id}|{role_id}".encode()
        base_index = int(hashlib.sha256(key).hexdigest(), 16) % self.config.persons
        
        idx = base_index
        i = 1
        while idx in self.reserved_indices:
            idx = (base_index + i * i) % self.config.persons
            i += 1
            
        self.reserved_indices.add(idx)
        self.role_to_index[role_id] = idx
        return idx


def assign_scenarios(config: ProfileConfig, seed_bank: SeedBank, manifests: Optional[Dict[str, Any]] = None) -> tuple[List[Dict[str, Any]], RoleResolver]:
    """Return a lightweight population index and the role resolver."""
    dist = config.scenario_dist
    rng: np.random.Generator = seed_bank.get("scenario")

    n = config.persons
    classes = ["normal", "suspicious", "confirmed_pattern", "false_positive"]
    weights = [dist.normal, dist.suspicious, dist.confirmed_pattern, dist.false_positive]

    # Pre-generate stochastic assignments so the stream doesn't shift
    class_assignments = rng.choice(classes, size=n, p=weights)
    total_days = config.total_days

    resolver = RoleResolver(config)
    population = [None] * n

    # 1. Manifest Reservation
    if manifests and "investigations" in manifests:
        for case in manifests["investigations"].get("cases", []):
            scenario_id = case["case_id"]
            for role in case.get("roles", []):
                role_id = role["role_id"]
                idx = resolver.resolve(scenario_id, role_id)
                
                # Force population[idx] to match role requirements
                population[idx] = {
                    "person_index":     idx,
                    "person_id":        make_uuid("civix-large-person", config.seed, idx),
                    "scenario_class":   "confirmed_pattern",
                    "scenario_family":  case.get("scenario_family", "organized_crime"),
                    "scenario_id_str":  scenario_id,
                    "scenario_category": "crime",
                    "difficulty":       "VERY_HIGH",
                    "target_cdrs":      int(role.get("target_cdrs", 500)),
                    "home_region":      0,
                    "active_start_day": 0,
                    "active_end_day":   config.total_days - 1,
                    "risk_score":       0.99,
                    "logical_role":     role_id
                }

    # 2. Stochastic fill
    for i in range(n):
        if population[i] is not None:
            continue
            
        sc_class = class_assignments[i]
        sc = rng.choice(_BY_CLASS[sc_class])
        act_min, act_max = ACTIVITY_PROFILES[sc_class]
        activity = int(rng.integers(act_min, act_max))

        n_regions = len(
            ["ajmer","jaipur","jodhpur","kota","bikaner","udaipur","alwar","sikar","bharatpur","pali"]
            if config.geography == "multi_region" else ["ajmer"]
        )
        home_region = int(rng.integers(0, n_regions))

        active_start = int(rng.integers(0, max(1, total_days // 4)))
        active_end = int(rng.integers(max(active_start + 1, total_days // 2), total_days))

        risk_score = round(float(rng.uniform(
            0.6 if sc_class == "confirmed_pattern" else
            0.3 if sc_class == "suspicious" else
            0.0,
            1.0 if sc_class == "confirmed_pattern" else
            0.7 if sc_class == "suspicious" else
            0.4
        )), 3)

        population[i] = {
            "person_index":     i,
            "person_id":        make_uuid("civix-large-person", config.seed, i),
            "scenario_class":   sc_class,
            "scenario_family":  sc["type"],
            "scenario_id_str":  sc["id"],
            "scenario_category": sc["category"],
            "difficulty":       sc["difficulty"],
            "target_cdrs":      activity,
            "home_region":      home_region,
            "active_start_day": active_start,
            "active_end_day":   active_end,
            "risk_score":       risk_score,
        }
        
    return population, resolver

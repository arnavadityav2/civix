"""
CIVIX Synthetic World V2: Behavioral Traits → Generation Parameters
civix_generator/v2/behavioral_traits.py

Translates latent traits into concrete generation parameters.
This is the only place where latent traits become numbers used for generation.

KEY RULE: The mapping must not produce scenario-specific constant values.
The output parameters are BEHAVIORALLY derived, not label-derived.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, List

# CDR count per-day range per occupation pattern
# These are realistic ranges — NOT scenario-specific
_OCCUPATION_CDR_RATES = {
    "office":    (0.8,  12.0),   # calls/day (mean per business day)
    "shift":     (0.5,  10.0),
    "irregular": (0.2,  20.0),
    "business":  (2.0,  40.0),   # business users call much more
    "retired":   (0.2,   5.0),
}

# Duration ranges by relationship type (NOT scenario)
# family = longer calls, business = shorter, criminal_coordination = very short
_RELATIONSHIP_DURATIONS = {
    "family":           (120, 900),    # 2–15 min
    "social":           (60,  600),    # 1–10 min
    "business":         (30,  300),    # 0.5–5 min
    "weak_tie":         (15,  180),    # 15s–3 min
    "criminal_coord":   (10,   90),    # very short bursts
    "unknown":          (20,  300),
}

# Income band → transaction amount parameters
# (log_mean_INR, log_std_INR) — lognormal distribution
_INCOME_TXN_PARAMS = {
    0: (8.0, 0.8),    # very_low  → exp(8)   ≈ 3,000 INR mean
    1: (9.0, 0.9),    # low       → exp(9)   ≈ 8,100 INR mean
    2: (9.8, 1.0),    # middle    → exp(9.8) ≈ 18,000 INR mean
    3: (10.8, 1.1),   # high      → exp(10.8)≈ 49,000 INR mean
    4: (12.0, 1.3),   # very_high → exp(12)  ≈ 162,000 INR mean
}

# Transaction types by income band (UPI dominates low income, RTGS for high)
_INCOME_TXN_TYPE_PROBS = {
    0: {"UPI": 0.55, "IMPS": 0.25, "NEFT": 0.10, "CASH_DEPOSIT": 0.07, "RTGS": 0.02, "CHEQUE": 0.01},
    1: {"UPI": 0.45, "IMPS": 0.30, "NEFT": 0.15, "CASH_DEPOSIT": 0.05, "RTGS": 0.03, "CHEQUE": 0.02},
    2: {"UPI": 0.35, "IMPS": 0.30, "NEFT": 0.20, "CASH_DEPOSIT": 0.05, "RTGS": 0.07, "CHEQUE": 0.03},
    3: {"UPI": 0.20, "IMPS": 0.25, "NEFT": 0.30, "CASH_DEPOSIT": 0.03, "RTGS": 0.18, "CHEQUE": 0.04},
    4: {"UPI": 0.10, "IMPS": 0.15, "NEFT": 0.35, "CASH_DEPOSIT": 0.02, "RTGS": 0.33, "CHEQUE": 0.05},
}


def get_cdr_target(
    person: Dict[str, Any],
    total_days: int,
    target_cdrs_per_person: float,
    rng: np.random.Generator,
) -> int:
    """
    Compute the target CDR count for a person.

    Derived from latent traits, NOT from scenario class directly.
    The comm_activity trait biases the count but does not determine it.
    """
    comm  = person["_comm_activity"]        # [0..1]
    occ   = person["_occupation"]
    biz   = person["_is_business"]
    active_days = max(1, person["active_end_day"] - person["active_start_day"])

    # Base rate from occupation
    lo, hi = _OCCUPATION_CDR_RATES.get(occ, (0.5, 15.0))

    # Blend occupation range with comm_activity trait
    # A high comm_activity person tends toward the hi end, but with noise
    base_rate = lo + comm * (hi - lo)

    # Business boost
    if biz:
        base_rate *= rng.uniform(1.3, 2.5)

    # Total CDRs = rate × active_days × noise
    noise = rng.lognormal(mean=0.0, sigma=0.4)   # ±40% lognormal noise
    n_cdrs = int(base_rate * active_days * noise)

    # Clamp to a wide but plausible range
    n_cdrs = int(np.clip(n_cdrs, 1, int(active_days * 60)))   # max 60 calls/day

    return n_cdrs


def get_call_duration(
    relationship_type: str,
    rng: np.random.Generator,
) -> int:
    """
    Sample a call duration based on the relationship type between caller/callee.
    NOT based on scenario class.
    """
    lo, hi = _RELATIONSHIP_DURATIONS.get(relationship_type, _RELATIONSHIP_DURATIONS["unknown"])
    # Lognormal within the band — realistic heavy tail
    raw = rng.lognormal(
        mean=np.log((lo + hi) / 2),
        sigma=0.5
    )
    return int(np.clip(raw, lo, hi))


def get_txn_amount(
    income_band: int,
    txn_type: str,
    rng: np.random.Generator,
) -> float:
    """
    Sample a transaction amount from a lognormal distribution
    parameterized by income band.
    NOT parameterized by scenario class.
    """
    log_mean, log_std = _INCOME_TXN_PARAMS.get(income_band, _INCOME_TXN_PARAMS[2])
    raw = float(rng.lognormal(log_mean, log_std))
    # RTGS minimum is 2 lakhs (200,000 INR)
    if txn_type == "RTGS":
        raw = max(raw, 200_000.0)
    # Clamp to realistic bounds
    raw = float(np.clip(raw, 10.0, 50_000_000.0))
    # Round to nearest 10
    return round(raw / 10) * 10


def get_txn_type(income_band: int, rng: np.random.Generator) -> str:
    """Sample transaction type by income band."""
    probs = _INCOME_TXN_TYPE_PROBS.get(income_band, _INCOME_TXN_TYPE_PROBS[2])
    types = list(probs.keys())
    weights = list(probs.values())
    return str(rng.choice(types, p=weights))


def get_txn_target(
    person: Dict[str, Any],
    rng: np.random.Generator,
) -> int:
    """
    Compute target transaction count for a person.
    Derived from latent traits (fin_activity, income_band, is_business, txn_freq).
    """
    fin   = person["_fin_activity"]
    freq  = person["_txn_freq_per_day"]
    biz   = person["_is_business"]
    active_days = max(1, person["active_end_day"] - person["active_start_day"])

    base = freq * active_days * (0.5 + fin)

    if biz:
        base *= rng.uniform(1.5, 4.0)

    noise = rng.lognormal(0.0, 0.35)
    n_txns = int(np.clip(base * noise, 1, active_days * 20))
    return n_txns

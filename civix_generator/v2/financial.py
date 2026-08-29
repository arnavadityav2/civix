"""
CIVIX Synthetic World V2: Financial Generator (Income-Band Aware)
civix_generator/v2/financial.py

Generates accounts and transactions parameterized by latent traits,
NOT by scenario class.

Key differences from V1:
- Transaction volume derived from fin_activity + txn_freq traits
- Transaction amounts from lognormal by income_band (not Pareto by scenario)
- Transaction types by income_band (not scenario)
- Some suspicious financial patterns applied stochastically (not deterministically)
- The same financial patterns can appear in different scenario classes
"""
from __future__ import annotations
import datetime
import numpy as np
from typing import Any, Dict, Iterator, List, Tuple

from .config import V2ProfileConfig
from .seeds import V2SeedBank, make_uuid
from .behavioral_traits import get_txn_target, get_txn_amount, get_txn_type

_BANKS = [
    "SBI", "PNB", "HDFC", "ICICI", "Axis", "BOB", "UCO", "Canara",
    "Union", "IDBI", "Yes", "Kotak", "IndusInd", "Federal", "RBL",
]
_ACCT_TYPES = ["SAVINGS", "CURRENT", "JOINT", "FIXED_DEPOSIT", "OVERDRAFT"]
_ACCT_WEIGHTS = [0.63, 0.22, 0.08, 0.05, 0.02]


def generate_accounts_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate financial accounts."""
    rng = seed_bank.get("account")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    n_accounts = config.accounts
    n_persons  = len(population)

    for i in range(n_accounts):
        acct_id    = make_uuid("civix-v2-account", config.seed, i)
        bank       = str(rng.choice(_BANKS))
        atype      = str(rng.choice(_ACCT_TYPES, p=_ACCT_WEIGHTS))

        holder_idx = int(rng.integers(0, n_persons))
        holder_id  = population[holder_idx]["person_id"]

        # Joint accounts: probability slightly higher for high social connectivity
        social = float(population[holder_idx].get("_social", 0.4))
        joint_prob = 0.05 + 0.10 * social
        joint_holder_id = None
        if rng.random() < joint_prob:
            second_idx = int(rng.integers(0, n_persons))
            joint_holder_id = population[second_idx]["person_id"]
            atype = "JOINT"

        masked = f"{bank}-****{rng.integers(1000, 9999)}"

        batch.append({
            "account_id":         acct_id,
            "account_index":      i,
            "bank":               bank,
            "account_type":       atype,
            "masked_number":      masked,
            "primary_holder_id":  holder_id,
            "joint_holder_id":    joint_holder_id,
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


# ── Suspicious financial pattern types ────────────────────────────────────────
# These are assigned stochastically — not deterministically by scenario.
# Some normal persons can exhibit these patterns (hard negatives).
SUSPICIOUS_FIN_PATTERNS = [
    "layering",        # rapid movement through accounts
    "structuring",     # just-below-threshold deposits
    "circular",        # A→B→C→A transfers
    "burst",           # many transactions in 48h
    "dormant_reactivation",  # long gap then large deposits
    "pass_through",    # near-identical inflow/outflow
]


def _assign_financial_pattern(
    person: Dict[str, Any],
    rng: np.random.Generator,
) -> str:
    """
    Assign a financial behavioral pattern.
    Criminals have a higher probability of suspicious patterns,
    but some normal persons also exhibit them (hard negatives).
    """
    sc  = person["scenario_class"]
    fin = float(person["_fin_activity"])

    if sc == "confirmed_pattern":
        # Higher probability of suspicious pattern, but not 100%
        if rng.random() < 0.55:
            return str(rng.choice(SUSPICIOUS_FIN_PATTERNS))
    elif sc == "suspicious":
        if rng.random() < 0.30:
            return str(rng.choice(SUSPICIOUS_FIN_PATTERNS))
    elif sc in ("normal", "false_positive"):
        # Hard negatives: 8% of normal/fp exhibit suspicious patterns
        if rng.random() < 0.08:
            return str(rng.choice(SUSPICIOUS_FIN_PATTERNS))

    return "standard"


def generate_transactions_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    account_index: List[str],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Stream transaction records.
    Volume and amounts are derived from latent traits, NOT scenario class.
    Suspicious financial patterns are injected stochastically.
    """
    rng = seed_bank.get("transaction")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    n_accounts   = len(account_index)
    start_dt     = config.date_start_dt
    total_days   = config.total_days
    target_total = config.target_transactions
    n_persons    = len(population)

    # ── Pre-compute per-person transaction targets ────────────────────────────
    raw_targets = [get_txn_target(p, rng) for p in population]
    raw_arr = np.array(raw_targets, dtype=np.float64)
    if raw_arr.sum() > 0:
        scale   = target_total / raw_arr.sum()
        targets = np.round(raw_arr * scale).astype(np.int64)
        targets = np.maximum(targets, 1)
        diff    = target_total - int(targets.sum())
        if diff > 0:
            targets[:diff] += 1
        elif diff < 0:
            targets[:-diff] -= 1
    else:
        targets = np.ones(n_persons, dtype=np.int64)

    txn_global_idx = 0

    for pop in population:
        n_txns = int(targets[pop["person_index"]])
        if n_txns == 0:
            continue

        income_band = int(pop.get("_income_band", 2))
        sc_class    = pop["scenario_class"]
        pattern     = _assign_financial_pattern(pop, rng)
        act_start   = int(pop["active_start_day"])
        act_end     = min(int(pop["active_end_day"]), total_days - 1)
        person_acct_idx = pop["person_index"] % n_accounts
        sender_id = account_index[person_acct_idx]

        # Burst: concentrate in a 48h window
        if pattern == "burst":
            burst_day = int(rng.integers(act_start, max(act_start + 1, act_end)))
            day_range = (burst_day, min(burst_day + 2, act_end))
        else:
            day_range = (act_start, act_end)

        for j in range(n_txns):
            day  = int(rng.integers(day_range[0], max(day_range[0] + 1, day_range[1])))
            hour = int(rng.integers(6, 23))
            ts   = datetime.datetime.combine(
                start_dt + datetime.timedelta(days=day),
                datetime.time(hour, int(rng.integers(0, 60)))
            )

            # Receiver
            recv_offset = int(rng.integers(1, min(50, n_accounts)))
            receiver_id = account_index[(person_acct_idx + recv_offset) % n_accounts]

            # Amount: from income-band lognormal, with pattern overrides
            if pattern == "structuring":
                # Just below 50,000 threshold — but with noise (not fixed)
                amount = float(rng.uniform(43_000, 49_800))
            elif pattern == "circular" and j % 3 == 2:
                # Round-trip back amount (similar to inflow, with noise)
                amount = float(rng.uniform(80_000, 200_000))
            elif pattern == "dormant_reactivation" and j == n_txns - 1:
                # Large final deposit
                amount = float(rng.uniform(200_000, 2_000_000))
            else:
                txn_type_for_amount = get_txn_type(income_band, rng)
                amount = get_txn_amount(income_band, txn_type_for_amount, rng)

            txn_type = get_txn_type(income_band, rng)
            txn_id   = make_uuid("civix-v2-txn", config.seed, txn_global_idx)

            batch.append({
                "transaction_id":      txn_id,
                "txn_index":           txn_global_idx,
                "sender_account_id":   sender_id,
                "receiver_account_id": receiver_id,
                "amount":              round(float(amount), 2),
                "currency":            "INR",
                "transaction_type":    txn_type,
                "timestamp":           ts.isoformat(),
                "year":                ts.year,
                "month":               ts.month,
                "sender_person_id":    pop["person_id"],
                "financial_pattern":   pattern,   # for audit only, not for ML features
            })
            txn_global_idx += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch

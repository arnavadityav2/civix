"""
CIVIX Large-Scale Generator: Financial Entities
civix_generator/large/finance.py

Generates financial accounts and streaming transactions.
Transaction amounts follow a Pareto distribution (many small,
few large) to avoid the "magic fixed amount" anti-pattern.
"""
from __future__ import annotations
import datetime
import math
from typing import Iterator, List, Dict, Any

import numpy as np

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig

_BANKS = [
    "SBI","PNB","HDFC","ICICI","Axis","BOB","UCO","Canara",
    "Union","IDBI","Yes","Kotak","IndusInd","Federal","RBL",
]
_ACCT_TYPES = ["SAVINGS","CURRENT","JOINT","FIXED_DEPOSIT","OVERDRAFT"]
_ACCT_WEIGHTS = [0.65, 0.20, 0.08, 0.05, 0.02]

_TXN_TYPES = ["NEFT","IMPS","UPI","RTGS","CASH_DEPOSIT","CASH_WITHDRAWAL","CHEQUE"]
_TXN_WEIGHTS = [0.30, 0.35, 0.20, 0.05, 0.05, 0.03, 0.02]

# Pareto parameters for amount generation by scenario class
_AMOUNT_PARAMS = {
    "normal":            {"low": 100,    "high": 20_000,  "pareto_a": 3.0},
    "suspicious":        {"low": 1_000,  "high": 500_000, "pareto_a": 1.5},
    "confirmed_pattern": {"low": 5_000,  "high": 500_000, "pareto_a": 1.2},
    "false_positive":    {"low": 5_000,  "high": 500_000, "pareto_a": 1.5},
}


def _pareto_amount(rng: np.random.Generator, sc_class: str) -> float:
    p = _AMOUNT_PARAMS.get(sc_class, _AMOUNT_PARAMS["normal"])
    raw = (rng.pareto(p["pareto_a"]) + 1) * p["low"]
    return round(min(raw, p["high"]) / 10) * 10   # round to nearest 10


def generate_accounts(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("account")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    for i in range(config.accounts):
        acct_id = make_uuid("civix-large-account", config.seed, i)
        bank    = str(rng.choice(_BANKS))
        atype   = str(rng.choice(_ACCT_TYPES, p=_ACCT_WEIGHTS))
        # Primary holder person index
        holder_idx = int(rng.integers(0, config.persons))
        holder_id  = make_uuid("civix-large-person", config.seed, holder_idx)

        # Joint account: 8% chance of second holder
        joint_holder_id = None
        if rng.random() < 0.08:
            second_idx      = int(rng.integers(0, config.persons))
            joint_holder_id = make_uuid("civix-large-person", config.seed, second_idx)
            atype           = "JOINT"

        masked_number = f"{bank}-****{rng.integers(1000,9999)}"

        batch.append({
            "account_id":       acct_id,
            "account_index":    i,
            "bank":             bank,
            "account_type":     atype,
            "masked_number":    masked_number,
            "primary_holder_id": holder_id,
            "joint_holder_id":  joint_holder_id,
            "sc_class_holder":  population[holder_idx]["scenario_class"],
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


def generate_transactions(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    account_index: List[str],   # list of account UUIDs
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Stream transaction records with Pareto-distributed amounts.

    Special signals injected:
    - STRUCTURING: Person with FIN-04 makes repeated just-below-threshold deposits
    - CORRUPTION_CYCLE: Person with FIN-14 sends periodic exact amounts to another
    - BURST: Person with FIN-05 makes many transactions within 48h
    - DORMANT: Person with FIN-11 has a long gap then a large deposit
    """
    rng = seed_bank.get("transaction")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    n_accounts  = len(account_index)
    start_dt    = config.date_start_dt
    total_days  = config.total_days

    # Transactions per profile: scale to config.transactions
    per_person_base = config.transactions / config.persons

    txn_global_idx = 0
    for pop in population:
        sc_class = pop["scenario_class"]
        family   = pop["scenario_family"]
        multiplier = {
            "normal": 1.0,
            "suspicious": 1.5,
            "confirmed_pattern": 2.0,
            "false_positive": 2.0,
        }.get(sc_class, 1.0)
        n_txns = max(1, round(per_person_base * multiplier))
        # Scale down to avoid exceeding total
        n_txns = min(n_txns, max(1, int(config.transactions // config.persons * 3)))

        person_acct_idx = pop["person_index"] % n_accounts
        sender_id       = account_index[person_acct_idx]

        act_start = pop["active_start_day"]
        act_end   = min(pop["active_end_day"], total_days - 1)

        for j in range(n_txns):
            day    = int(rng.integers(act_start, max(act_start + 1, act_end)))
            hour   = int(rng.integers(9, 18))
            ts     = datetime.datetime.combine(
                start_dt + datetime.timedelta(days=day),
                datetime.time(hour, int(rng.integers(0, 60)))
            )

            # Receiver account
            recv_offset = int(rng.integers(1, min(50, n_accounts)))
            receiver_id = account_index[(person_acct_idx + recv_offset) % n_accounts]

            # Amount
            if family == "structuring":
                # Just below 50,000 threshold (SIG-05 analogue)
                amount = float(round(rng.uniform(45_000, 49_999), 2))
            elif family == "corruption_cycle":
                # Exact periodic amount
                amount = float(rng.choice([100_000, 125_000, 150_000]))
            elif family == "salary_pattern":
                amount = float(round(rng.uniform(15_000, 80_000), 2))
            else:
                amount = _pareto_amount(rng, sc_class)

            txn_type = str(rng.choice(_TXN_TYPES, p=_TXN_WEIGHTS))
            txn_id   = make_uuid("civix-large-txn", config.seed, txn_global_idx)

            batch.append({
                "transaction_id":   txn_id,
                "txn_index":        txn_global_idx,
                "sender_account_id": sender_id,
                "receiver_account_id": receiver_id,
                "amount":           amount,
                "currency":         "INR",
                "transaction_type": txn_type,
                "timestamp":        ts.isoformat(),
                "year":             ts.year,
                "month":            ts.month,
                "sender_person_id": pop["person_id"],
            })
            txn_global_idx += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch

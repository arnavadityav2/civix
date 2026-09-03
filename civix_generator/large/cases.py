"""
CIVIX Large-Scale Generator: Cases, FIRs, Roles
civix_generator/large/cases.py
"""
from __future__ import annotations
import datetime
from typing import Iterator, List, Dict, Any

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig

_CASE_TYPES = [
    "FRAUD","THEFT","ROBBERY","ASSAULT","MISSING_PERSON",
    "ORGANIZED_CRIME","FINANCIAL_CRIME","CYBER_FRAUD",
    "PROPERTY_CRIME","VEHICLE_CRIME","TRAFFICKING","EXTORTION",
    "IDENTITY_FRAUD","SUSPICIOUS_DEATH","KIDNAPPING",
]
_CASE_STATUS = ["OPEN","UNDER_INVESTIGATION","CLOSED_SOLVED","CLOSED_UNSOLVED","SUSPENDED"]
_STATUS_WEIGHTS = [0.30, 0.40, 0.15, 0.10, 0.05]
_PRIORITY = ["CRITICAL","HIGH","MEDIUM","LOW"]
_PRIORITY_WEIGHTS = [0.05, 0.20, 0.50, 0.25]
_ROLES = ["SUSPECT","ACCUSED","WITNESS","VICTIM","INFORMANT","ASSOCIATE"]
_ROLE_WEIGHTS = [0.30, 0.15, 0.25, 0.20, 0.05, 0.05]


def generate_cases(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("case")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    start_dt   = config.date_start_dt
    total_days = config.total_days

    for i in range(config.cases):
        case_id   = make_uuid("civix-large-case", config.seed, i)
        case_type = str(rng.choice(_CASE_TYPES))
        status    = str(rng.choice(_CASE_STATUS, p=_STATUS_WEIGHTS))
        priority  = str(rng.choice(_PRIORITY, p=_PRIORITY_WEIGHTS))
        day_open  = int(rng.integers(0, max(1, total_days - 30)))
        opened_at = (start_dt + datetime.timedelta(days=day_open)).isoformat()

        # Assign 1-8 persons to this case
        n_involved = int(rng.integers(1, 9))
        involved   = []
        for _ in range(n_involved):
            p_idx = int(rng.integers(0, config.persons))
            role  = str(rng.choice(_ROLES, p=_ROLE_WEIGHTS))
            involved.append({
                "person_id": make_uuid("civix-large-person", config.seed, p_idx),
                "role": role,
            })

        batch.append({
            "case_id":     case_id,
            "case_index":  i,
            "case_type":   case_type,
            "status":      status,
            "priority":    priority,
            "opened_at":   opened_at,
            "n_involved":  n_involved,
            "involved":    str(involved),   # serialised for Parquet compatibility
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


def generate_case_entity_roles(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """One record per (case, entity, role) triple."""
    rng = seed_bank.get("case")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    for i in range(config.cases):
        case_id     = make_uuid("civix-large-case", config.seed, i)
        n_involved  = int(rng.integers(1, 9))
        for _ in range(n_involved):
            p_idx   = int(rng.integers(0, config.persons))
            role    = str(rng.choice(_ROLES, p=_ROLE_WEIGHTS))
            cer_id  = make_uuid("civix-large-cer", config.seed, i, p_idx, role)
            batch.append({
                "cer_id":    cer_id,
                "case_id":   case_id,
                "person_id": make_uuid("civix-large-person", config.seed, p_idx),
                "role":      role,
            })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch

"""
CIVIX Large-Scale Generator: Telecom Entities
civix_generator/large/telecom.py

Generates: phone numbers, SIM cards, devices, SIM-in-device
assignments, SIM-number assignments, and CDR events.

CDR generation is the performance-critical path (75M rows for
Profile C). It is fully streaming — never holds more than
`config.batch_size` records in memory.
"""
from __future__ import annotations
import datetime
import math
from typing import Iterator, List, Dict, Any, Optional

import numpy as np

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig

# ─── Phone number pool ────────────────────────────────────────────────────────
_OPERATORS = ["Airtel", "Jio", "BSNL", "Vi", "MTNL"]
_ISD_PREFIXES = ["+91"]

# Call duration distributions (seconds) per activity type
_DURATION_PARAMS = {
    "normal":            (60,  300),   # mean 60s to 5min
    "suspicious":        (30,  120),
    "confirmed_pattern": (20,  90),
    "false_positive":    (120, 600),
}


def generate_phones(
    config: ProfileConfig,
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("phone")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    for i in range(config.phone_numbers):
        ph_id = make_uuid("civix-large-phone", config.seed, i)
        # 10-digit number starting with 6-9
        lead  = int(rng.integers(6, 10))
        rest  = int(rng.integers(100_000_000, 999_999_999))
        number = f"{lead}{rest:09d}"
        operator = str(rng.choice(_OPERATORS))
        batch.append({
            "phone_id":     ph_id,
            "phone_index":  i,
            "number":       number,
            "operator":     operator,
            "is_recycled":  bool(rng.random() < 0.02),
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


def generate_sims(
    config: ProfileConfig,
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("sim")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    for i in range(config.sims):
        sim_id = make_uuid("civix-large-sim", config.seed, i)
        iccid  = f"8991{rng.integers(10**14, 10**15 - 1):014d}"
        batch.append({
            "sim_id":    sim_id,
            "sim_index": i,
            "iccid":     iccid,
            "is_burner": bool(rng.random() < 0.05),
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


def generate_devices(
    config: ProfileConfig,
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("device")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    _BRANDS  = ["Samsung","Xiaomi","Realme","Vivo","Oppo","Nokia","Motorola","OnePlus"]
    _TYPES   = ["SMARTPHONE","FEATURE_PHONE","TABLET"]
    _T_WGTS  = [0.75, 0.20, 0.05]

    for i in range(config.devices):
        dev_id = make_uuid("civix-large-device", config.seed, i)
        imei   = f"{rng.integers(10**14, 10**15 - 1):015d}"
        brand  = str(rng.choice(_BRANDS))
        dtype  = str(rng.choice(_TYPES, p=_T_WGTS))
        batch.append({
            "device_id":    dev_id,
            "device_index": i,
            "imei":         imei,
            "brand":        brand,
            "device_type":  dtype,
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch


# ─── CDR Generation ──────────────────────────────────────────────────────────

def _hour_weight() -> np.ndarray:
    """Return a 24-element probability array for realistic call times."""
    # Peaks at morning (8-9), noon (12-13), evening (17-19), night (20-22)
    w = np.array([
        0.2, 0.1, 0.1, 0.1, 0.1, 0.2,   # 0-5
        0.5, 1.2, 2.5, 2.0, 1.5, 1.8,   # 6-11
        2.0, 1.5, 1.2, 1.5, 1.8, 2.5,   # 12-17
        3.0, 3.2, 2.8, 2.2, 1.5, 0.8,   # 18-23
    ], dtype=float)
    return w / w.sum()


_HOUR_WEIGHTS = _hour_weight()
_HOURS = np.arange(24)

_CALL_TYPES  = ["VOICE","SMS","DATA"]
_CALL_WEIGHTS = [0.65, 0.25, 0.10]


def generate_cdrs(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    phone_index: List[str],       # list of phone UUIDs for random selection
    cell_index: List[str],        # list of cell sector UUIDs
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Stream CDR records.

    Strategy:
    - Each person is assigned a target CDR count from their scenario profile.
    - We scale all targets proportionally so the total matches config.cdrs.
    - CDRs are generated in person-order, streamed in batches of config.batch_size.
    - For each CDR: pick a callee from the same cohort (social graph effect),
      pick a timestamp within the person's active period,
      pick a cell sector near the person's home region.
    """
    rng = seed_bank.get("cdr")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    start_dt = config.date_start_dt
    n_phones  = len(phone_index)
    n_cells   = len(cell_index)
    total_days = config.total_days

    # Scale activity counts to exactly hit config.cdrs
    raw_targets = [p["target_cdrs"] for p in population]
    raw_sum = sum(raw_targets)
    scale = config.cdrs / raw_sum if raw_sum > 0 else 1.0
    targets = [max(1, round(t * scale)) for t in raw_targets]

    cdr_global_idx = 0
    for pop, n_cdrs in zip(population, targets):
        caller_phone_idx = pop["person_index"] % n_phones
        caller_phone_id  = phone_index[caller_phone_idx]
        sc_class         = pop["scenario_class"]
        home_region      = pop["home_region"]
        act_start        = pop["active_start_day"]
        act_end          = min(pop["active_end_day"], total_days - 1)
        dur_min, dur_max = _DURATION_PARAMS.get(sc_class, (60, 300))

        # For geo-anomaly scenarios: ~10% of CDRs use a distant cell
        is_geo_anomaly = sc_class in ("suspicious", "confirmed_pattern") and pop["scenario_family"] in ("geo_anomaly", "tower_hopping", "coordinated_comm", "silent_then_burst")

        # Determine local cells (cells near home region)
        cells_per_region = max(1, n_cells // 10)
        local_cell_start = home_region * cells_per_region
        local_cells = cell_index[local_cell_start : local_cell_start + cells_per_region] or cell_index[:cells_per_region]

        for j in range(n_cdrs):
            # Timestamp
            day_offset = int(rng.integers(act_start, max(act_start + 1, act_end)))
            hour       = int(rng.choice(_HOURS, p=_HOUR_WEIGHTS))
            minute     = int(rng.integers(0, 60))
            second     = int(rng.integers(0, 60))
            ts_date    = start_dt + datetime.timedelta(days=day_offset)
            ts         = datetime.datetime.combine(ts_date, datetime.time(hour, minute, second))

            # Callee
            callee_offset = int(rng.integers(1, min(50, len(population))))
            callee_idx    = (pop["person_index"] + callee_offset) % len(population)
            callee_phone_id = phone_index[callee_idx % n_phones]

            # Duration
            duration_sec = int(rng.integers(dur_min, dur_max))

            # Cell sector
            if is_geo_anomaly and rng.random() < 0.10:
                # Distant cell (anomalous signal)
                distant_start = ((home_region + 5) % 10) * cells_per_region
                distant_cells = cell_index[distant_start : distant_start + cells_per_region] or cell_index
                cell_id = str(rng.choice(distant_cells))
            else:
                cell_id = str(rng.choice(local_cells))

            call_type = str(rng.choice(_CALL_TYPES, p=_CALL_WEIGHTS))

            cdr_id = make_uuid("civix-large-cdr", config.seed, cdr_global_idx)
            batch.append({
                "cdr_id":           cdr_id,
                "caller_phone_id":  caller_phone_id,
                "callee_phone_id":  callee_phone_id,
                "timestamp":        ts.isoformat(),
                "year":             ts.year,
                "month":            ts.month,
                "duration_seconds": duration_sec,
                "call_type":        call_type,
                "cell_sector_id":   cell_id,
                "caller_person_id": pop["person_id"],
            })
            cdr_global_idx += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch

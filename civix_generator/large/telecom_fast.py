"""
CIVIX Large-Scale Generator: Vectorized CDR Generator (v4)
civix_generator/large/telecom_fast.py

Uses NumPy datetime64 arithmetic for fully vectorized timestamp generation.
No Python datetime objects or per-record Python loops in the hot path.

Key optimization: timestamps are generated as numpy datetime64, then
converted to ISO strings using numpy's built-in string formatting —
completely eliminating the 75M timedelta() calls that caused the slowdown.

Throughput target: >15,000 CDRs/sec on Dell G15 (single CPU core).
"""
from __future__ import annotations
import numpy as np
from typing import Iterator, List, Dict, Any

from .seeds import SeedBank
from .config import ProfileConfig


_HOUR_WEIGHTS = np.array([
    0.2, 0.1, 0.1, 0.1, 0.1, 0.2,
    0.5, 1.2, 2.5, 2.0, 1.5, 1.8,
    2.0, 1.5, 1.2, 1.5, 1.8, 2.5,
    3.0, 3.2, 2.8, 2.2, 1.5, 0.8,
], dtype=float)
_HOUR_WEIGHTS /= _HOUR_WEIGHTS.sum()

_CALL_TYPES_ARR = np.array(["VOICE", "SMS", "DATA"])
_CALL_PROBS     = np.array([0.65, 0.25, 0.10])

_DUR_RANGES = {
    "normal":            (60,  300),
    "suspicious":        (30,  120),
    "confirmed_pattern": (20,   90),
    "false_positive":    (120, 600),
}

_GEO_ANOMALY_FAMILIES = frozenset({
    "geo_anomaly", "tower_hopping", "coordinated_comm", "silent_then_burst"
})


def _numpy_dates_to_iso(start_date_np64: np.datetime64, day_offsets: np.ndarray,
                         hours: np.ndarray, minutes: np.ndarray,
                         seconds: np.ndarray) -> np.ndarray:
    """Vectorized ISO timestamp generation using numpy datetime64.

    Returns an array of ISO timestamp strings like '2024-03-15T14:22:07'.
    No Python datetime objects created — pure numpy string ops.
    """
    # Add day offsets to start date (datetime64 arithmetic is vectorized)
    base = start_date_np64 + day_offsets.astype("timedelta64[D]")
    # Convert to seconds since epoch then add intra-day offset
    secs_in_day = (hours.astype(np.int64) * 3600
                   + minutes.astype(np.int64) * 60
                   + seconds.astype(np.int64)).astype("timedelta64[s]")
    timestamps = base.astype("datetime64[D]").astype("datetime64[s]") + secs_in_day
    # numpy formats datetime64[s] as 'YYYY-MM-DDTHH:MM:SS' — exact ISO8601
    return timestamps.astype(str)


def generate_cdrs_fast(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    phone_index: List[str],
    cell_index: List[str],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Fully vectorized CDR generator (v4).

    All timestamp math is numpy datetime64.
    Inner dict-building loop still exists but operates on pre-computed arrays —
    no timedelta, no datetime, no strftime in the hot path.
    """
    rng = seed_bank.get("cdr")

    n_persons  = len(population)
    n_phones   = len(phone_index)
    n_cells    = len(cell_index)
    total_days = config.total_days
    BATCH      = config.batch_size

    # numpy datetime64 start date (for vectorized arithmetic)
    start_date_np64 = np.datetime64(config.date_start, "D")

    # -- Scale activity targets to hit config.cdrs exactly ------------------
    raw     = np.array([p["target_cdrs"] for p in population], dtype=np.float64)
    targets = np.round(raw * config.cdrs / raw.sum()).astype(np.int64)
    targets = np.maximum(targets, 1)
    diff    = config.cdrs - int(targets.sum())
    if diff > 0:
        targets[:diff] += 1
    elif diff < 0:
        targets[:-diff] -= 1

    # -- Pre-compute per-person fixed attributes ----------------------------
    person_ids       = np.array([p["person_id"]       for p in population], dtype=object)
    caller_ph_idx    = np.arange(n_persons) % n_phones
    phone_arr        = np.array(phone_index, dtype=object)
    cell_arr         = np.array(cell_index,  dtype=object)
    caller_phone_ids = phone_arr[caller_ph_idx]

    home_regions  = np.array([p["home_region"]      for p in population], dtype=np.int32)
    active_starts = np.array([p["active_start_day"] for p in population], dtype=np.int32)
    active_ends   = np.clip(
        np.array([p["active_end_day"] for p in population], dtype=np.int32),
        active_starts + 1,
        total_days - 1,
    )
    sc_classes = [p["scenario_class"]  for p in population]
    families   = [p["scenario_family"] for p in population]

    dur_min = np.array([_DUR_RANGES.get(sc, (60, 300))[0] for sc in sc_classes], dtype=np.int32)
    dur_max = np.array([_DUR_RANGES.get(sc, (60, 300))[1] for sc in sc_classes], dtype=np.int32)

    is_geo_anomaly = np.array([
        sc in ("suspicious", "confirmed_pattern") and fam in _GEO_ANOMALY_FAMILIES
        for sc, fam in zip(sc_classes, families)
    ], dtype=bool)

    n_regions        = 10 if config.geography == "multi_region" else 1
    cells_per_region = max(1, n_cells // n_regions)

    # -- Generate -----------------------------------------------------------
    batch: List[Dict[str, Any]] = []
    cdr_global_idx = 0

    for person_i in range(n_persons):
        n = int(targets[person_i])
        if n == 0:
            continue

        a_start = int(active_starts[person_i])
        a_end   = int(active_ends[person_i])
        dur_lo  = int(dur_min[person_i])
        dur_hi  = max(dur_lo + 1, int(dur_max[person_i]))

        # -- All numpy arrays per person (no Python loops) --
        day_offsets = rng.integers(a_start, a_end + 1, size=n, dtype=np.int32)
        hours       = rng.choice(24, size=n, p=_HOUR_WEIGHTS).astype(np.int32)
        minutes     = rng.integers(0, 60, size=n, dtype=np.int32)
        seconds     = rng.integers(0, 60, size=n, dtype=np.int32)
        durations   = rng.integers(dur_lo, dur_hi, size=n, dtype=np.int32)
        ct_idxs     = rng.choice(3, size=n, p=_CALL_PROBS)
        call_types  = _CALL_TYPES_ARR[ct_idxs]

        callee_offsets = rng.integers(1, min(51, n_persons), size=n, dtype=np.int32)
        callee_idxs    = (person_i + callee_offsets) % n_persons
        callee_ph_ids  = phone_arr[callee_idxs % n_phones]

        # -- Vectorized cell sector assignment --
        home_r      = int(home_regions[person_i])
        loc_start   = home_r * cells_per_region
        local_cells = cell_arr[loc_start: loc_start + cells_per_region]
        if len(local_cells) == 0:
            local_cells = cell_arr[:cells_per_region]

        if bool(is_geo_anomaly[person_i]):
            distant_start = ((home_r + 5) % n_regions) * cells_per_region
            distant_cells = cell_arr[distant_start: distant_start + cells_per_region]
            if len(distant_cells) == 0:
                distant_cells = cell_arr[:cells_per_region]
            use_distant  = rng.random(size=n) < 0.10
            local_idxs   = rng.integers(0, len(local_cells),   size=n, dtype=np.int32)
            distant_idxs = rng.integers(0, len(distant_cells), size=n, dtype=np.int32)
            cell_ids     = np.where(use_distant, distant_cells[distant_idxs], local_cells[local_idxs])
        else:
            cell_ids = local_cells[rng.integers(0, len(local_cells), size=n, dtype=np.int32)]

        # -- Fully vectorized ISO timestamp generation (no timedelta!) --
        ts_arr = _numpy_dates_to_iso(start_date_np64, day_offsets, hours, minutes, seconds)
        # ts_arr[j] looks like '2024-03-15T14:22:07'

        # -- year/month extraction from string (faster than datetime parse) --
        years  = day_offsets  # placeholder; we extract from ts_arr
        # Use numpy string slicing: ts_arr[:,0:4] for year, ts_arr[:,5:7] for month
        yr_arr = ts_arr.astype("U10")  # first 10 chars = 'YYYY-MM-DD'

        # -- Build dict batch (Python loop, but all values are pre-computed numpy scalars) --
        caller_phone_id  = str(caller_phone_ids[person_i])
        caller_person_id = str(person_ids[person_i])
        base_offset      = cdr_global_idx

        for j in range(n):
            ts = str(ts_arr[j])
            batch.append({
                "cdr_id":            f"cdr-{config.seed}-{base_offset + j}",
                "caller_phone_id":   caller_phone_id,
                "callee_phone_id":   str(callee_ph_ids[j]),
                "timestamp":         ts,
                "year":              int(ts[0:4]),
                "month":             int(ts[5:7]),
                "duration_seconds":  int(durations[j]),
                "call_type":         str(call_types[j]),
                "cell_sector_id":    str(cell_ids[j]),
                "caller_person_id":  caller_person_id,
            })
            cdr_global_idx += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch

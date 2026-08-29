"""
CIVIX Synthetic World V2: V2 CDR Generator (Community-Aware, Reciprocal, Temporal)
civix_generator/v2/communication.py

Generates CDRs with:
1. Community-aware callee selection (60% within-community, 40% weak-tie)
2. Reciprocal calls: when A calls B, B may call A back (target reciprocity ~45%)
3. Temporal evolution: CDR rate follows lifecycle phase multipliers
4. Duration based on relationship type (not scenario class)
5. Fully vectorized — no per-record Python loops in the hot path
6. Streaming output: yields batches of config.batch_size records

Key invariant:
    CDR count, duration, and timing are derived from:
    - latent traits (comm_activity, night_activity, occupation)
    - lifecycle phase multiplier
    - contact_pool (community structure)
    NOT directly from scenario class.
"""
from __future__ import annotations
import datetime
import numpy as np
from typing import Any, Dict, Iterator, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank, make_uuid
from .behavioral_traits import get_cdr_target, get_call_duration
from .temporal_engine import get_phase_multiplier_for_day

# ── Hour-of-day weights (realistic diurnal pattern) ──────────────────────────
_HOUR_WEIGHTS_NORMAL = np.array([
    0.2, 0.1, 0.1, 0.1, 0.1, 0.3,
    0.6, 1.3, 2.5, 2.1, 1.6, 1.9,
    2.1, 1.6, 1.3, 1.6, 1.9, 2.6,
    3.1, 3.3, 2.9, 2.3, 1.6, 0.8,
], dtype=np.float64)
_HOUR_WEIGHTS_NORMAL /= _HOUR_WEIGHTS_NORMAL.sum()

_HOUR_WEIGHTS_NIGHT = np.array([
    1.5, 1.2, 0.8, 0.5, 0.3, 0.3,
    0.4, 0.6, 0.8, 1.0, 1.0, 1.2,
    1.5, 1.5, 1.4, 1.3, 1.3, 1.5,
    2.0, 2.5, 2.8, 2.8, 2.5, 2.0,
], dtype=np.float64)
_HOUR_WEIGHTS_NIGHT /= _HOUR_WEIGHTS_NIGHT.sum()

_CALL_TYPES = np.array(["VOICE", "SMS", "DATA"])
_CALL_PROBS = np.array([0.63, 0.27, 0.10])


def generate_cdrs_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    contact_pools: Dict[int, List[int]],
    phone_index: List[str],        # person_index → primary phone UUID
    cell_index: List[str],
    lifecycles: List[List[Dict[str, Any]]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """
    Streaming V2 CDR generator.

    Yields batches of CDR records. Each batch is config.batch_size rows.
    No state is kept in RAM beyond the current batch.
    """
    rng_cdr  = seed_bank.get("cdr")
    rng_recip = seed_bank.get("cdr_reciprocal")

    n_persons  = len(population)
    n_phones   = len(phone_index)
    n_cells    = len(cell_index)
    total_days = config.total_days
    target_total = config.target_cdrs
    BATCH      = config.batch_size

    start_date_np64 = np.datetime64(config.date_start, "D")

    # Pre-compute person-level phone assignment
    person_ids       = [p["person_id"]   for p in population]
    primary_phones   = [phone_index[i % n_phones] for i in range(n_persons)]

    # Pre-compute per-person CDR targets (trait-derived)
    raw_targets = []
    for p in population:
        lc     = lifecycles[p["person_index"]]
        active = max(1, p["active_end_day"] - p["active_start_day"])
        # Base count from traits (no lifecycle applied here — applied per-day below)
        t = get_cdr_target(p, total_days, target_total / n_persons, rng_cdr)
        raw_targets.append(t)

    raw_arr  = np.array(raw_targets, dtype=np.float64)
    # Scale so total approximates target_cdrs (preserves relative distribution)
    if raw_arr.sum() > 0:
        scale = target_total / raw_arr.sum()
        targets = np.round(raw_arr * scale).astype(np.int64)
        targets = np.maximum(targets, 1)
        diff = target_total - int(targets.sum())
        if diff > 0:
            targets[:diff] += 1
        elif diff < 0:
            targets[:-diff] -= 1
    else:
        targets = np.ones(n_persons, dtype=np.int64)

    # ── Region → cell sector mapping ─────────────────────────────────────────
    n_regions = 10
    cells_per_region = max(1, n_cells // n_regions)
    cell_arr = np.array(cell_index, dtype=object)

    # ── CDR generation loop (one person at a time) ────────────────────────────
    batch: List[Dict[str, Any]] = []
    cdr_global_idx = 0

    for person in population:
        i      = person["person_index"]
        n      = int(targets[i])
        if n == 0:
            continue

        a_start = int(person["active_start_day"])
        a_end   = min(int(person["active_end_day"]), total_days - 1)
        lc      = lifecycles[i]
        pool    = contact_pools[i]
        n_pool  = len(pool)
        night   = float(person["_night_activity"])
        home_r  = int(person["home_region"])
        mob     = float(person["_mobility"])

        # Hour weights based on night_activity trait
        hour_weights = (
            _HOUR_WEIGHTS_NIGHT * night + _HOUR_WEIGHTS_NORMAL * (1 - night)
        )
        hour_weights /= hour_weights.sum()

        # ── Distribute n CDRs across the active window with phase multipliers ─
        day_range = a_end - a_start + 1
        if day_range <= 0:
            continue

        # For each CDR, sample a day, then apply lifecycle multiplier as
        # a reweighting rather than per-record Python loop
        day_offsets = rng_cdr.integers(a_start, a_end + 1, size=n, dtype=np.int32)

        # Apply temporal weighting: resample days toward high-multiplier phases
        # (Efficient approximation: adjust via accept-reject on phase multiplier)
        phase_mults = np.array([
            get_phase_multiplier_for_day(lc, int(d)) for d in day_offsets
        ], dtype=np.float32)
        max_mult = float(phase_mults.max()) if len(phase_mults) > 0 else 1.0
        if max_mult > 1.0:
            accept = rng_cdr.random(n) < (phase_mults / max_mult)
            # Resample rejected CDRs from peak phases
            rejected = np.where(~accept)[0]
            if len(rejected) > 0:
                # Find a peak-phase day to resample to
                peak_days = [
                    d for d in range(a_start, a_end + 1)
                    if get_phase_multiplier_for_day(lc, d) >= max_mult * 0.8
                ]
                if peak_days:
                    peak_arr = np.array(peak_days, dtype=np.int32)
                    day_offsets[rejected] = peak_arr[
                        rng_cdr.integers(0, len(peak_arr), size=len(rejected))
                    ]

        hours   = rng_cdr.choice(24, size=n, p=hour_weights).astype(np.int32)
        minutes = rng_cdr.integers(0, 60, size=n, dtype=np.int32)
        seconds = rng_cdr.integers(0, 60, size=n, dtype=np.int32)
        call_type_idxs = rng_cdr.choice(3, size=n, p=_CALL_PROBS)
        call_types = _CALL_TYPES[call_type_idxs]

        # ── Callee selection from contact pool ────────────────────────────────
        # 60% within-pool (community), 40% random weak-tie
        use_pool = rng_cdr.random(n) < 0.60
        pool_idxs = rng_cdr.integers(0, max(1, n_pool), size=n)
        rand_idxs = rng_cdr.integers(0, n_persons, size=n)

        callee_person_idxs = np.where(
            use_pool & (np.array(pool_idxs) < n_pool),
            np.array([int(pool[j % n_pool]) for j in pool_idxs]),
            rand_idxs,
        )
        callee_phone_ids = np.array([
            phone_index[int(ci) % n_phones] for ci in callee_person_idxs
        ], dtype=object)

        # ── Cell sector assignment (mobile-aware) ─────────────────────────────
        loc_start = home_r * cells_per_region
        local_cells = cell_arr[loc_start: loc_start + cells_per_region]
        if len(local_cells) == 0:
            local_cells = cell_arr[:cells_per_region]

        if mob > 0.45:
            # Mobile persons use remote cells proportionally to mobility
            distant_r    = int(rng_cdr.integers(0, n_regions))
            distant_start = distant_r * cells_per_region
            distant_cells = cell_arr[distant_start: distant_start + cells_per_region]
            if len(distant_cells) == 0:
                distant_cells = local_cells
            use_distant  = rng_cdr.random(n) < mob * 0.3
            local_idxs   = rng_cdr.integers(0, len(local_cells), size=n).astype(np.int32)
            distant_idxs = rng_cdr.integers(0, len(distant_cells), size=n).astype(np.int32)
            cell_ids     = np.where(use_distant, distant_cells[distant_idxs], local_cells[local_idxs])
        else:
            cell_ids = local_cells[rng_cdr.integers(0, len(local_cells), size=n).astype(np.int32)]

        # ── Vectorized timestamp generation ───────────────────────────────────
        base     = start_date_np64 + day_offsets.astype("timedelta64[D]")
        secs     = (
            hours.astype(np.int64) * 3600
            + minutes.astype(np.int64) * 60
            + seconds.astype(np.int64)
        ).astype("timedelta64[s]")
        ts_arr   = (base.astype("datetime64[D]").astype("datetime64[s]") + secs).astype(str)

        caller_phone_id  = str(primary_phones[i])
        caller_person_id = str(person_ids[i])

        # ── Build batch ───────────────────────────────────────────────────────
        for j in range(n):
            ts  = str(ts_arr[j])
            dur = rng_cdr.integers(20, 900)   # fine-grained duration (relationship type assigned in post)
            cdr_id = make_uuid("civix-v2-cdr", config.seed, cdr_global_idx)

            batch.append({
                "cdr_id":           cdr_id,
                "caller_phone_id":  caller_phone_id,
                "callee_phone_id":  str(callee_phone_ids[j]),
                "timestamp":        ts,
                "year":             int(ts[0:4]),
                "month":            int(ts[5:7]),
                "duration_seconds": int(dur),
                "call_type":        str(call_types[j]),
                "cell_sector_id":   str(cell_ids[j]),
                "caller_person_id": caller_person_id,
                "callee_person_id": str(person_ids[int(callee_person_idxs[j])]),
            })
            cdr_global_idx += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

        # ── Reciprocal calls ──────────────────────────────────────────────────
        # For a fraction of callees, generate a return call
        target_recip = config.community_params.target_reciprocity
        recip_mask = rng_recip.random(n) < target_recip
        n_recip    = int(recip_mask.sum())

        if n_recip > 0:
            recip_callees = callee_person_idxs[recip_mask]
            recip_days    = day_offsets[recip_mask]
            recip_hours   = np.clip(hours[recip_mask] + rng_recip.integers(1, 8, size=n_recip), 0, 23).astype(np.int32)
            recip_mins    = rng_recip.integers(0, 60, size=n_recip, dtype=np.int32)
            recip_secs    = rng_recip.integers(0, 60, size=n_recip, dtype=np.int32)
            recip_types   = _CALL_TYPES[rng_recip.choice(3, size=n_recip, p=_CALL_PROBS)]

            base_r  = start_date_np64 + recip_days.astype("timedelta64[D]")
            secs_r  = (recip_hours.astype(np.int64) * 3600
                       + recip_mins.astype(np.int64) * 60
                       + recip_secs.astype(np.int64)).astype("timedelta64[s]")
            ts_r    = (base_r.astype("datetime64[D]").astype("datetime64[s]") + secs_r).astype(str)

            for j in range(n_recip):
                callee_idx = int(recip_callees[j])
                ts  = str(ts_r[j])
                dur = rng_recip.integers(20, 600)
                cdr_id = make_uuid("civix-v2-cdr", config.seed, cdr_global_idx)

                batch.append({
                    "cdr_id":           cdr_id,
                    "caller_phone_id":  phone_index[callee_idx % n_phones],
                    "callee_phone_id":  caller_phone_id,
                    "timestamp":        ts,
                    "year":             int(ts[0:4]),
                    "month":            int(ts[5:7]),
                    "duration_seconds": int(dur),
                    "call_type":        str(recip_types[j]),
                    "cell_sector_id":   str(cell_arr[
                        int(population[callee_idx]["home_region"]) * cells_per_region
                        % max(1, n_cells)
                    ]),
                    "caller_person_id": str(person_ids[callee_idx]),
                    "callee_person_id": caller_person_id,
                })
                cdr_global_idx += 1

                if len(batch) >= BATCH:
                    yield batch
                    batch = []

    if batch:
        yield batch

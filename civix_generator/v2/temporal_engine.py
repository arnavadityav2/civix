"""
CIVIX Synthetic World V2: Temporal Lifecycle Engine
civix_generator/v2/temporal_engine.py

Assigns each person a lifecycle consisting of named phases.
Each phase has a start/end day and a CDR/transaction rate multiplier.

Lifecycle phases:
    baseline    → ordinary behavior per latent traits
    activation  → new contacts appear, slight volume increase
    escalation  → volume increases toward peak
    peak        → maximum activity
    cooldown    → activity decreases
    dormancy    → very low activity

Key invariant:
    Normal persons mostly stay in baseline.
    Criminal actors may progress through multiple phases,
    OR stay in baseline forever (low-visibility criminals).
    The lifecycle does NOT directly encode labels into features —
    it creates temporal patterns that overlap across classes.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, List, Tuple

from .config import V2ProfileConfig, TemporalParams
from .seeds import V2SeedBank

# Phase type → multiplier on baseline CDR rate
PHASE_MULTIPLIERS = {
    "baseline":   1.0,
    "activation": 1.3,
    "escalation": 1.8,
    "peak":       2.5,
    "cooldown":   1.2,
    "dormancy":   0.2,
}


def assign_lifecycles(
    population: List[Dict[str, Any]],
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> List[List[Dict[str, Any]]]:
    """
    Returns a list of lifecycle phase lists, one per person.
    lifecycle[i] = [
        {"phase": "baseline", "start_day": 0, "end_day": 400, "multiplier": 1.0},
        {"phase": "activation", "start_day": 401, "end_day": 500, "multiplier": 1.3},
        ...
    ]

    Each person's active window is divided into phases.
    The multiplier is applied to CDR/transaction rate during that phase.
    """
    rng = seed_bank.get("lifecycle")
    tp  = config.temporal_params
    total_days = config.total_days

    lifecycles: List[List[Dict[str, Any]]] = []

    for person in population:
        sc      = person["scenario_class"]
        start   = person["active_start_day"]
        end     = person["active_end_day"]
        span    = max(30, end - start)

        phases = _assign_phases(sc, start, end, span, rng, tp, person)
        lifecycles.append(phases)

    return lifecycles


def _assign_phases(
    scenario_class: str,
    start: int,
    end: int,
    span: int,
    rng: np.random.Generator,
    tp: TemporalParams,
    person: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build lifecycle phases for one person."""

    # ── Determine lifecycle template ─────────────────────────────────────────
    # Normal: baseline only (with low probability of activation)
    if scenario_class == "normal":
        if rng.random() < tp.normal_activation_rate:
            return _two_phase(start, end, span, rng, "baseline", "activation")
        else:
            return [_phase("baseline", start, end, 1.0)]

    # False positive: baseline + possible burst
    if scenario_class == "false_positive":
        if rng.random() < 0.40:
            return _two_phase(start, end, span, rng, "baseline", "peak")
        return [_phase("baseline", start, end, 1.0)]

    # Suspicious: baseline + escalation, or just baseline
    if scenario_class == "suspicious":
        if rng.random() < tp.suspicious_escalation_rate:
            return _multi_phase(start, end, span, rng,
                                ["baseline", "escalation", "cooldown"])
        else:
            return [_phase("baseline", start, end, 1.0)]

    # Confirmed pattern:
    if scenario_class == "confirmed_pattern":
        # Low-visibility criminals stay in baseline
        if rng.random() < tp.low_visibility_criminal_rate:
            return [_phase("baseline", start, end, 1.0)]
        # Dormant then burst: long dormancy, then peak
        if rng.random() < 0.15:
            return _dormant_burst(start, end, span, rng)
        # Full lifecycle
        return _multi_phase(start, end, span, rng,
                            ["baseline", "activation", "escalation", "peak", "cooldown"])

    # Fallback
    return [_phase("baseline", start, end, 1.0)]


def _phase(name: str, start: int, end: int, mult: float) -> Dict[str, Any]:
    return {"phase": name, "start_day": start, "end_day": end,
            "multiplier": PHASE_MULTIPLIERS.get(name, mult)}


def _two_phase(
    start: int, end: int, span: int,
    rng: np.random.Generator,
    phase1: str, phase2: str,
) -> List[Dict[str, Any]]:
    """Split into two phases at a random midpoint."""
    split = start + int(rng.integers(span // 3, span * 2 // 3))
    split = min(split, end - 5)
    return [
        _phase(phase1, start, split, PHASE_MULTIPLIERS[phase1]),
        _phase(phase2, split + 1, end, PHASE_MULTIPLIERS[phase2]),
    ]


def _multi_phase(
    start: int, end: int, span: int,
    rng: np.random.Generator,
    phase_names: List[str],
) -> List[Dict[str, Any]]:
    """Divide active window into N phases with random but ordered boundaries."""
    n = len(phase_names)
    if span < n * 5:
        return [_phase(phase_names[0], start, end, PHASE_MULTIPLIERS[phase_names[0]])]

    # Generate n-1 sorted boundary points
    raw = sorted(rng.integers(start + 5, end - 5, size=n - 1).tolist())
    boundaries = [start] + raw + [end]

    phases = []
    for i, name in enumerate(phase_names):
        s = boundaries[i]
        e = boundaries[i + 1]
        if s >= e:
            continue
        phases.append(_phase(name, s, e, PHASE_MULTIPLIERS[name]))

    if not phases:
        phases = [_phase(phase_names[0], start, end, PHASE_MULTIPLIERS[phase_names[0]])]
    return phases


def _dormant_burst(
    start: int, end: int, span: int,
    rng: np.random.Generator,
) -> List[Dict[str, Any]]:
    """Long dormancy period followed by a peak burst."""
    if span < 60:
        return [_phase("baseline", start, end, 1.0)]
    burst_start = start + int(rng.integers(span * 2 // 3, span * 9 // 10))
    burst_start = min(burst_start, end - 10)
    return [
        _phase("dormancy", start, burst_start, PHASE_MULTIPLIERS["dormancy"]),
        _phase("peak",     burst_start + 1, end, PHASE_MULTIPLIERS["peak"]),
    ]


def get_phase_multiplier_for_day(lifecycle: List[Dict[str, Any]], day: int) -> float:
    """Return the rate multiplier for a given day number."""
    for phase in lifecycle:
        if phase["start_day"] <= day <= phase["end_day"]:
            return float(phase["multiplier"])
    return 1.0


def get_lifecycle_stats(lifecycles: List[List[Dict[str, Any]]]) -> Dict[str, Any]:
    """Return summary statistics for a batch of lifecycles."""
    phase_counts: Dict[str, int] = {}
    for lc in lifecycles:
        for phase in lc:
            name = phase["phase"]
            phase_counts[name] = phase_counts.get(name, 0) + 1
    total = sum(phase_counts.values())
    return {
        "phase_distribution": {k: v / total for k, v in phase_counts.items()},
        "total_phase_assignments": total,
        "unique_persons": len(lifecycles),
    }

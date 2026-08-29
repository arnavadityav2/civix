"""
CIVIX Large-Scale Generator: Profile Configurations
civix_generator/large/config.py

Defines the four dataset profiles and all configurable parameters.
Nothing in this file should be hardcoded in generator logic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import datetime

# ─── Scenario class distribution ─────────────────────────────────────────────

@dataclass
class ScenarioDist:
    """Fractional weights (must sum to 1.0)."""
    normal:           float = 0.70   # No investigative signal
    suspicious:       float = 0.15   # Anomalous but ambiguous
    confirmed_pattern: float = 0.10  # Planted signal with ground-truth label
    false_positive:   float = 0.05   # Looks bad, is innocent

    def validate(self):
        total = self.normal + self.suspicious + self.confirmed_pattern + self.false_positive
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"ScenarioDist weights must sum to 1.0, got {total}")


# ─── Noise rates ──────────────────────────────────────────────────────────────

@dataclass
class NoiseCfg:
    missing_values_rate:  float = 0.010   # 1% of optional fields null
    timestamp_jitter_sec: int   = 60      # ± seconds on non-critical timestamps
    duplicate_cdr_rate:   float = 0.002   # 0.2% duplicate CDRs (labelled)
    ocr_error_rate:       float = 0.003   # Name/address OCR-style typos


# ─── Profile definition ───────────────────────────────────────────────────────

@dataclass
class ProfileConfig:
    name:        str
    seed:        int

    # Entity counts
    persons:      int
    organizations: int
    devices:      int
    sims:         int
    phone_numbers: int
    accounts:     int
    properties:   int
    vehicles:     int
    locations:    int      # synthetic points beyond Ajmer
    cell_sectors: int      # synthetic cell sectors beyond the 47 canonical

    # Event counts
    cdrs:         int
    transactions: int
    cases:        int

    # Time window
    date_start: str   # ISO date, e.g. "2024-01-01"
    date_end:   str   # ISO date, e.g. "2024-06-30"

    # Generation tuning
    batch_size:          int = 100_000   # max records in memory at once
    shard_rows:          int = 1_000_000 # rows per Parquet file shard
    geography:           str = "multi_region"  # "ajmer" | "multi_region"
    checkpoint_interval: int = 10        # flush checkpoint every N shards

    # Distributions
    scenario_dist: ScenarioDist = field(default_factory=ScenarioDist)
    noise:         NoiseCfg     = field(default_factory=NoiseCfg)

    @property
    def date_start_dt(self) -> datetime.date:
        return datetime.date.fromisoformat(self.date_start)

    @property
    def date_end_dt(self) -> datetime.date:
        return datetime.date.fromisoformat(self.date_end)

    @property
    def total_days(self) -> int:
        return (self.date_end_dt - self.date_start_dt).days + 1


# ─── Canonical profile definitions ───────────────────────────────────────────

PROFILES: Dict[str, ProfileConfig] = {

    "A": ProfileConfig(
        name="development",
        seed=20260829,
        persons=1_000,
        organizations=80,
        devices=1_500,
        sims=1_800,
        phone_numbers=1_800,
        accounts=900,
        properties=1_800,
        vehicles=600,
        locations=200,
        cell_sectors=150,
        cdrs=250_000,
        transactions=50_000,
        cases=100,
        date_start="2025-01-01",
        date_end="2025-06-30",
        batch_size=50_000,
        shard_rows=250_000,
    ),

    "B": ProfileConfig(
        name="validation",
        seed=20260829,
        persons=10_000,
        organizations=600,
        devices=15_000,
        sims=18_000,
        phone_numbers=18_000,
        accounts=9_000,
        properties=18_000,
        vehicles=6_000,
        locations=1_000,
        cell_sectors=800,
        cdrs=2_500_000,
        transactions=500_000,
        cases=1_000,
        date_start="2024-01-01",
        date_end="2024-12-31",
        batch_size=100_000,
        shard_rows=1_000_000,
    ),

    "C": ProfileConfig(
        name="training",
        seed=20260829,
        persons=250_000,
        organizations=10_000,
        devices=375_000,
        sims=450_000,
        phone_numbers=450_000,
        accounts=225_000,
        properties=450_000,
        vehicles=150_000,
        locations=15_000,
        cell_sectors=8_000,
        cdrs=75_000_000,
        transactions=15_000_000,
        cases=25_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=100_000,
        shard_rows=1_000_000,
    ),

    "D": ProfileConfig(
        name="stress",
        seed=20260829,
        persons=5_000_000,
        organizations=200_000,
        devices=7_500_000,
        sims=9_000_000,
        phone_numbers=9_000_000,
        accounts=4_500_000,
        properties=9_000_000,
        vehicles=3_000_000,
        locations=500_000,
        cell_sectors=200_000,
        cdrs=1_500_000_000,
        transactions=300_000_000,
        cases=500_000,
        date_start="2020-01-01",
        date_end="2024-12-31",
        batch_size=100_000,
        shard_rows=1_000_000,
    ),
}


import copy

def get_profile(name: str) -> ProfileConfig:
    key = name.upper()
    if key not in PROFILES:
        raise ValueError(f"Unknown profile '{name}'. Valid: {list(PROFILES)}")
    # Return a deep copy so that _apply_smoke() mutations are instance-local
    return copy.deepcopy(PROFILES[key])

"""
CIVIX Synthetic World V2: Configuration
civix_generator/v2/config.py

All parameters for the V2 generator.
Nothing scenario-specific is hardcoded in behavioral generators.
"""
from __future__ import annotations
import copy
import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


# ── Scenario distribution ──────────────────────────────────────────────────────

@dataclass
class ScenarioDist:
    """Fractional weights (must sum to 1.0)."""
    normal:            float = 0.70
    suspicious:        float = 0.15
    confirmed_pattern: float = 0.10
    false_positive:    float = 0.05

    def validate(self):
        total = self.normal + self.suspicious + self.confirmed_pattern + self.false_positive
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"ScenarioDist must sum to 1.0, got {total:.6f}")


# ── Latent trait parameters ───────────────────────────────────────────────────

@dataclass
class LatentTraitParams:
    """
    Beta distribution parameters (α, β) per scenario class for each trait.
    Distributions MUST substantially overlap across classes.
    These are biases on the same latent space, not separate spaces.
    """
    # (alpha, beta) for Beta distribution → mean = α/(α+β)
    # communication_activity
    comm_activity: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (2.0, 4.0),   # mean ≈ 0.33
        "suspicious":        (3.0, 3.0),   # mean ≈ 0.50
        "confirmed_pattern": (4.0, 2.5),   # mean ≈ 0.62
        "false_positive":    (3.5, 2.0),   # mean ≈ 0.64  (contaminated normal)
    })
    # financial_activity
    fin_activity: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (2.0, 4.5),   # mean ≈ 0.31
        "suspicious":        (2.5, 3.0),   # mean ≈ 0.45
        "confirmed_pattern": (3.0, 3.0),   # mean ≈ 0.50
        "false_positive":    (3.5, 2.5),   # mean ≈ 0.58
    })
    # mobility
    mobility: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (1.5, 4.0),   # mean ≈ 0.27
        "suspicious":        (2.0, 3.0),   # mean ≈ 0.40
        "confirmed_pattern": (2.5, 2.5),   # mean ≈ 0.50
        "false_positive":    (2.0, 2.5),   # mean ≈ 0.44
    })
    # social_connectivity
    social: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (2.0, 3.5),   # mean ≈ 0.36
        "suspicious":        (2.5, 3.0),   # mean ≈ 0.45
        "confirmed_pattern": (3.0, 2.5),   # mean ≈ 0.55
        "false_positive":    (3.5, 2.0),   # mean ≈ 0.64
    })
    # night_activity
    night: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (1.5, 6.0),   # mean ≈ 0.20
        "suspicious":        (2.0, 4.5),   # mean ≈ 0.31
        "confirmed_pattern": (2.5, 4.0),   # mean ≈ 0.38
        "false_positive":    (1.8, 5.0),   # mean ≈ 0.26
    })
    # device_stability  (1.0 = stable, 0.0 = churns frequently)
    device_stability: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (5.0, 2.0),   # mean ≈ 0.71
        "suspicious":        (3.0, 3.0),   # mean ≈ 0.50
        "confirmed_pattern": (2.5, 3.5),   # mean ≈ 0.42
        "false_positive":    (4.0, 2.5),   # mean ≈ 0.62
    })
    # network_centrality_tendency
    centrality: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        "normal":            (1.5, 4.5),   # mean ≈ 0.25
        "suspicious":        (2.0, 3.5),   # mean ≈ 0.36
        "confirmed_pattern": (2.5, 3.0),   # mean ≈ 0.45
        "false_positive":    (2.0, 3.0),   # mean ≈ 0.40
    })


# ── Community parameters ──────────────────────────────────────────────────────

@dataclass
class CommunityParams:
    """Controls community structure generation."""
    # Fraction of persons who belong to a family community
    family_fraction: float = 0.85
    # Fraction of persons who belong to a workplace community
    workplace_fraction: float = 0.65
    # Fraction of persons who belong to a social group
    social_group_fraction: float = 0.40
    # Target reciprocity rate [fraction of call pairs that get return call]
    target_reciprocity: float = 0.45   # ± stochastic variation
    # Community size distributions (min, mode, max)
    family_size: Tuple[int, int, int] = (2, 4, 8)
    workplace_size: Tuple[int, int, int] = (10, 50, 200)
    social_size: Tuple[int, int, int] = (5, 15, 50)
    criminal_size: Tuple[int, int, int] = (3, 8, 25)
    # Fraction of within-community calls vs random weak-tie calls
    within_community_call_fraction: float = 0.60
    # Fraction of confirmed_pattern persons in criminal networks
    criminal_network_fraction: float = 0.80


# ── Temporal parameters ──────────────────────────────────────────────────────

@dataclass
class TemporalParams:
    """Controls lifecycle phase assignment."""
    # Fraction of normal persons who experience a lifecycle beyond baseline
    normal_activation_rate: float = 0.15
    # Fraction of suspicious persons who experience escalation
    suspicious_escalation_rate: float = 0.55
    # Fraction of confirmed_pattern who are low-visibility (stay in baseline)
    low_visibility_criminal_rate: float = 0.20
    # Phase multipliers (on top of baseline CDR rate)
    phase_multipliers: Dict[str, float] = field(default_factory=lambda: {
        "baseline":    1.0,
        "activation":  1.3,
        "escalation":  1.8,
        "peak":        2.5,
        "cooldown":    1.2,
        "dormancy":    0.2,
    })


# ── Adversarial / hard negative parameters ────────────────────────────────────

@dataclass
class AdversarialParams:
    """Controls hard negative injection and adversarial case generation."""
    # Fraction of normal persons receiving hard-negative boosts
    high_volume_legitimate_rate: float = 0.10   # call-center, business
    high_mobility_legitimate_rate: float = 0.05  # frequent traveler
    high_finance_legitimate_rate: float = 0.05   # business owner
    phone_churn_legitimate_rate: float = 0.05    # legitimate churn
    high_centrality_legitimate_rate: float = 0.05  # network hub
    burst_activity_legitimate_rate: float = 0.03  # 2-week burst
    # Low-visibility criminal fraction (within confirmed_pattern)
    low_visibility_criminal_rate: float = 0.20
    # Bridge node fraction (legitimate-looking intermediaries)
    bridge_node_rate: float = 0.05


# ── Noise config ──────────────────────────────────────────────────────────────

@dataclass
class NoiseCfg:
    missing_values_rate:  float = 0.008
    timestamp_jitter_sec: int   = 120
    duplicate_cdr_rate:   float = 0.001


# ── Main V2 profile config ────────────────────────────────────────────────────

@dataclass
class V2ProfileConfig:
    """Complete configuration for Synthetic World V2."""
    name:   str
    seed:   int
    version: str = "2.0.0"

    # Population
    persons:       int = 5_000
    organizations: int = 400

    # Telecom entities
    devices:       int = 7_000
    sims:          int = 8_500
    phone_numbers: int = 8_500
    accounts:      int = 4_500

    # Locations
    locations:    int = 1_000
    cell_sectors: int = 800

    # Event targets (approximate — actual depends on latent traits)
    target_cdrs:        int = 1_500_000
    target_transactions: int = 300_000

    # Time window
    date_start: str = "2022-01-01"
    date_end:   str = "2024-12-31"

    # Train/val/test temporal splits (as fraction of total_days)
    # TRAIN: start → train_end
    # VALIDATION: train_end → val_end
    # TEST: val_end → end
    train_end_frac: float = 0.60    # ~22 months
    val_end_frac:   float = 0.78    # ~6 more months

    # Generation tuning
    batch_size:  int = 50_000
    shard_rows:  int = 500_000

    # Sub-configs
    scenario_dist:      ScenarioDist      = field(default_factory=ScenarioDist)
    latent_params:      LatentTraitParams = field(default_factory=LatentTraitParams)
    community_params:   CommunityParams   = field(default_factory=CommunityParams)
    temporal_params:    TemporalParams    = field(default_factory=TemporalParams)
    adversarial_params: AdversarialParams = field(default_factory=AdversarialParams)
    noise:              NoiseCfg          = field(default_factory=NoiseCfg)

    @property
    def date_start_dt(self) -> datetime.date:
        return datetime.date.fromisoformat(self.date_start)

    @property
    def date_end_dt(self) -> datetime.date:
        return datetime.date.fromisoformat(self.date_end)

    @property
    def total_days(self) -> int:
        return (self.date_end_dt - self.date_start_dt).days + 1

    @property
    def train_cutoff_day(self) -> int:
        return int(self.total_days * self.train_end_frac)

    @property
    def val_cutoff_day(self) -> int:
        return int(self.total_days * self.val_end_frac)

    def validate(self):
        self.scenario_dist.validate()
        assert 0 < self.train_end_frac < self.val_end_frac < 1.0


# ── Canonical profiles ─────────────────────────────────────────────────────────

# Seed offsets for multi-seed generation
SEED_A = 20261001   # Primary training seed
SEED_B = 20261002   # Cross-generation eval seed 1
SEED_C = 20261003   # Cross-generation eval seed 2

V2_PROFILES: Dict[str, V2ProfileConfig] = {

    # Dev / smoke test (runs in < 3 minutes)
    "DEV": V2ProfileConfig(
        name="v2_dev",
        seed=SEED_A,
        persons=5_000,
        organizations=300,
        devices=7_000,
        sims=8_000,
        phone_numbers=8_000,
        accounts=4_000,
        locations=500,
        cell_sectors=400,
        target_cdrs=1_200_000,
        target_transactions=240_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=20_000,
        shard_rows=200_000,
    ),

    # Integration test
    "INT": V2ProfileConfig(
        name="v2_integration",
        seed=SEED_A,
        persons=50_000,
        organizations=3_000,
        devices=70_000,
        sims=85_000,
        phone_numbers=85_000,
        accounts=45_000,
        locations=5_000,
        cell_sectors=4_000,
        target_cdrs=12_000_000,
        target_transactions=2_500_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=50_000,
        shard_rows=500_000,
    ),

    # Full Profile V2 — SEED-A
    "V2A": V2ProfileConfig(
        name="v2_seed_a",
        seed=SEED_A,
        persons=250_000,
        organizations=10_000,
        devices=350_000,
        sims=425_000,
        phone_numbers=425_000,
        accounts=220_000,
        locations=15_000,
        cell_sectors=8_000,
        target_cdrs=75_000_000,
        target_transactions=15_000_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=100_000,
        shard_rows=1_000_000,
    ),

    # Cross-seed eval — SEED-B (50k for cross-gen test)
    "V2B": V2ProfileConfig(
        name="v2_seed_b",
        seed=SEED_B,
        persons=50_000,
        organizations=3_000,
        devices=70_000,
        sims=85_000,
        phone_numbers=85_000,
        accounts=45_000,
        locations=5_000,
        cell_sectors=4_000,
        target_cdrs=12_000_000,
        target_transactions=2_500_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=50_000,
        shard_rows=500_000,
    ),

    # Cross-seed eval — SEED-C (50k for cross-gen test)
    "V2C": V2ProfileConfig(
        name="v2_seed_c",
        seed=SEED_C,
        persons=50_000,
        organizations=3_000,
        devices=70_000,
        sims=85_000,
        phone_numbers=85_000,
        accounts=45_000,
        locations=5_000,
        cell_sectors=4_000,
        target_cdrs=12_000_000,
        target_transactions=2_500_000,
        date_start="2022-01-01",
        date_end="2024-12-31",
        batch_size=50_000,
        shard_rows=500_000,
    ),
}


def get_v2_profile(name: str) -> V2ProfileConfig:
    key = name.upper()
    if key not in V2_PROFILES:
        raise ValueError(f"Unknown V2 profile '{name}'. Valid: {list(V2_PROFILES)}")
    cfg = copy.deepcopy(V2_PROFILES[key])
    cfg.validate()
    return cfg

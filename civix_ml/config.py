"""
CIVIX ML — Central configuration.
All paths and defaults defined here. No hardcoded paths in modules.
"""
import os
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
ROOT_DIR      = Path(__file__).parent.parent
PROFILE_C_DIR = Path(os.environ.get("CIVIX_PROFILE_DIR", r"D:\civix_data\synthetic\profile_v2_v2a"))
FEATURES_DIR  = PROFILE_C_DIR / "features_v1"
MODELS_DIR    = Path(r"D:\civix_data\models")
REPORTS_DIR   = ROOT_DIR / "docs" / "phase3a"
EXPERIMENTS_DIR = MODELS_DIR / "experiments"

# ── Dataset Parquet paths ───────────────────────────────────────────────────
CDR_GLOB        = str(PROFILE_C_DIR / "cdrs" / "**" / "*.parquet")
TXN_GLOB        = str(PROFILE_C_DIR / "transactions" / "**" / "*.parquet")
PERSONS_GLOB    = str(PROFILE_C_DIR / "persons" / "*.parquet")
ACCOUNTS_GLOB   = str(PROFILE_C_DIR / "accounts" / "*.parquet")
PHONES_GLOB     = str(PROFILE_C_DIR / "phones" / "*.parquet")
SIMS_GLOB       = str(PROFILE_C_DIR / "sims" / "*.parquet")
DEVICES_GLOB    = str(PROFILE_C_DIR / "devices" / "*.parquet")
CELL_GLOB       = str(PROFILE_C_DIR / "cell_sectors" / "*.parquet")
LABELS_GLOB     = str(PROFILE_C_DIR / "ground_truth" / "person_labels" / "*.parquet")
SPLITS_GLOB     = str(PROFILE_C_DIR / "ground_truth" / "train_val_test_split" / "*.parquet")

# ── Temporal bounds ─────────────────────────────────────────────────────────
DATASET_START   = "2022-01-01"
DATASET_END     = "2024-12-31"
DEFAULT_AS_OF   = "2024-12-31"

# ── ML Settings ─────────────────────────────────────────────────────────────
GLOBAL_SEED     = 42
BATCH_SIZE      = 100_000
FEATURE_VERSION = "v1"

# ── Label definitions ────────────────────────────────────────────────────────
# Task A: Suspicious Entity Classification
# Positive class = confirmed_pattern
# Negative class = normal + suspicious + false_positive
POSITIVE_CLASS  = "confirmed_pattern"

# ── Night-call hours ─────────────────────────────────────────────────────────
NIGHT_START_HOUR = 22
NIGHT_END_HOUR   = 6

# ── GATE 4: Generator Artifact Features ───────────────────────────────────────────────
# These features have near-zero within-class variance (CV < 0.05).
# The synthetic generator hardcoded fixed values per scenario_class.
# Including them gives trivially perfect PR-AUC=1.0 — NOT real-world signal.
# Confirmed by artifact_scan.py: all have max_CV < 0.042.
GENERATOR_ARTIFACT_FEATURES = [
    "avg_duration_sec",      # hardcoded per scenario
    "std_duration_sec",      # derived from hardcoded duration
    "max_duration_sec",      # hardcoded per scenario
    "min_duration_sec",      # hardcoded per scenario
    "long_call_ratio",       # derived from hardcoded max_duration
    "total_txns",            # always 60/90/120 per scenario (std=0.0)
    "active_txn_days",       # always equal to total_txns / fixed_rate
    "txns_per_active_day",   # derived from total_txns
    "night_txn_ratio",       # hardcoded 0.0 per scenario
    "has_both_activity",     # binary, always 1.0 for all persons
    "night_activity_product",# always 0.0 (product of two zero-variance features)
]

# ── High-value transaction threshold (percentile-based, computed at runtime)
HIGH_VALUE_TXN_PERCENTILE = 95

# ── DuckDB performance tuning ────────────────────────────────────────────────
# C: drive has <5 GB free — point temp spill to D: drive
DUCKDB_TEMP_DIR    = r"D:\civix_tmp"
DUCKDB_MEMORY_LIMIT = "6GB"   # G15 has 16GB RAM, leave 10GB for OS + Python
DUCKDB_THREADS      = 2       # 2 threads = lowest possible peak memory pressure

# ── Ensure directories exist ─────────────────────────────────────────────────
for _d in [FEATURES_DIR, MODELS_DIR, REPORTS_DIR, EXPERIMENTS_DIR]:
    _d.mkdir(parents=True, exist_ok=True)
Path(DUCKDB_TEMP_DIR).mkdir(parents=True, exist_ok=True)

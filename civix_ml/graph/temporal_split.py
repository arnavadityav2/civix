"""
CIVIX Temporal Graph Splitting — Phase 3B
Ensures no future edges contaminate historical graph snapshots.
Every graph operation must specify as_of_timestamp.
"""
from pathlib import Path
from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection

log = get_logger(__name__)

# Official temporal boundaries matching the Phase 3A splits
# These are chosen based on the dataset spanning 2022-01-01 to 2024-12-31
TEMPORAL_SPLITS = {
    "TRAIN":      "2023-12-31",   # Training on activity up to end of 2023
    "VALIDATION": "2024-06-30",   # Validation on activity up to mid 2024
    "TEST":       "2024-12-31",   # Test on full dataset (full 3-year window)
}


def validate_temporal_graph(
    edge_parquet_glob: str,
    timestamp_col: str,
    as_of_timestamp: str,
    sample_size: int = 100_000,
) -> dict:
    """
    Verify no edge has timestamp > as_of_timestamp.
    Returns a result dict with passed=True/False and violation count.
    """
    con = get_connection()
    glob_fwd = edge_parquet_glob.replace("\\", "/")

    result = con.execute(f"""
        SELECT
            COUNT(*) AS total_checked,
            SUM(CASE WHEN {timestamp_col} > '{as_of_timestamp}' THEN 1 ELSE 0 END) AS violations,
            MAX({timestamp_col}) AS max_ts
        FROM (
            SELECT {timestamp_col}
            FROM read_parquet('{glob_fwd}')
            USING SAMPLE {sample_size}
        )
    """).fetchone()

    total, violations, max_ts = result
    passed = violations == 0

    out = {
        "passed":        passed,
        "as_of":         as_of_timestamp,
        "sample_size":   total,
        "violations":    violations,
        "max_timestamp": str(max_ts),
    }

    if not passed:
        log.error(
            f"TEMPORAL LEAKAGE DETECTED in {edge_parquet_glob}!\n"
            f"  {violations:,} edges have timestamp > {as_of_timestamp}\n"
            f"  Max timestamp found: {max_ts}\n"
            f"  FIX: re-filter edges with WHERE timestamp <= as_of_timestamp"
        )
    else:
        log.info(f"  Temporal gate PASSED: {edge_parquet_glob} — 0 violations in {total:,} samples")

    con.close()
    return out

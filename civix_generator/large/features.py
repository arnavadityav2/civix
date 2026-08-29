"""
CIVIX Large-Scale Generator: ML Feature Aggregator
civix_generator/large/features.py

Aggregates raw CDR/transaction records into per-person feature rows.
Reads from already-written Parquet shards using DuckDB (streaming, no RAM load).
Output goes into ml_features/ directory.

NOTE: All feature columns are derived ONLY from observable records.
      Ground truth labels are NEVER included here.
"""
from __future__ import annotations
import glob as _glob
import os
from typing import Any, Dict


def generate_person_behavior_features(
    parquet_dir: str,
    profile_name: str,
    output_dir: str,
) -> Dict[str, Any]:
    """
    Aggregate CDR + transaction Parquet files into per-person feature vectors.
    Uses DuckDB for out-of-core aggregation (does not load all records into RAM).

    Returns a summary dict: {feature_name: {status, path/error, bytes}}.
    """
    try:
        import duckdb
    except ImportError:
        raise RuntimeError(
            "DuckDB is required for feature aggregation. "
            "Install it with: pip install duckdb"
        )

    os.makedirs(output_dir, exist_ok=True)

    # -- Resolve actual Parquet files (handles both flat and hive layouts) --
    def _resolve_parquet(base: str) -> str:
        """Return a glob pattern that finds parquet files regardless of layout."""
        # Try hive-partitioned layout first (year=.../month=.../*.parquet)
        hive = os.path.join(base, "**", "*.parquet")
        flat = os.path.join(base, "*.parquet")
        # Use forward slashes for DuckDB on all platforms
        if _glob.glob(os.path.join(base, "year=*")):
            return hive.replace("\\", "/")
        elif _glob.glob(flat):
            return flat.replace("\\", "/")
        else:
            # Fallback: recursive glob — DuckDB will handle it
            return hive.replace("\\", "/")

    cdr_pattern = _resolve_parquet(os.path.join(parquet_dir, "cdrs"))
    txn_pattern = _resolve_parquet(os.path.join(parquet_dir, "transactions"))

    cdr_feat_path = os.path.join(output_dir, "person_communication_features.parquet").replace("\\", "/")
    txn_feat_path = os.path.join(output_dir, "person_financial_features.parquet").replace("\\", "/")

    # Determine if hive partitioning is present
    cdr_hive = bool(_glob.glob(os.path.join(parquet_dir, "cdrs", "year=*")))
    txn_hive = bool(_glob.glob(os.path.join(parquet_dir, "transactions", "year=*")))

    con = duckdb.connect(":memory:")

    # -- CDR features -------------------------------------------------------
    cdr_hive_opt = "hive_partitioning=true" if cdr_hive else "union_by_name=true"
    cdr_sql = f"""
    COPY (
        SELECT
            caller_person_id                    AS person_id,
            COUNT(*)                            AS total_calls,
            AVG(duration_seconds)               AS avg_call_duration_sec,
            STDDEV(duration_seconds)            AS std_call_duration_sec,
            COUNT(DISTINCT callee_phone_id)     AS unique_callees,
            COUNT(DISTINCT cell_sector_id)      AS unique_cell_sectors,
            COUNT(DISTINCT
                CAST(year AS VARCHAR) || '-' || LPAD(CAST(month AS VARCHAR),2,'0')
            )                                   AS active_months,
            SUM(CASE WHEN call_type = 'VOICE' THEN 1 ELSE 0 END) AS voice_calls,
            SUM(CASE WHEN call_type = 'SMS'   THEN 1 ELSE 0 END) AS sms_count,
            SUM(CASE WHEN call_type = 'DATA'  THEN 1 ELSE 0 END) AS data_sessions,
            MIN(timestamp) AS first_call_ts,
            MAX(timestamp) AS last_call_ts
        FROM read_parquet('{cdr_pattern}', {cdr_hive_opt})
        GROUP BY caller_person_id
    ) TO '{cdr_feat_path}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    # -- Transaction features -----------------------------------------------
    txn_hive_opt = "hive_partitioning=true" if txn_hive else "union_by_name=true"
    txn_sql = f"""
    COPY (
        SELECT
            sender_person_id                    AS person_id,
            COUNT(*)                            AS total_transactions,
            SUM(amount)                         AS total_sent_amount,
            AVG(amount)                         AS avg_txn_amount,
            MAX(amount)                         AS max_txn_amount,
            STDDEV(amount)                      AS std_txn_amount,
            COUNT(DISTINCT receiver_account_id) AS unique_receivers,
            COUNT(DISTINCT transaction_type)    AS txn_type_diversity,
            MIN(timestamp) AS first_txn_ts,
            MAX(timestamp) AS last_txn_ts
        FROM read_parquet('{txn_pattern}', {txn_hive_opt})
        GROUP BY sender_person_id
    ) TO '{txn_feat_path}' (FORMAT PARQUET, COMPRESSION SNAPPY)
    """

    results = {}
    for name, sql, out_path in [
        ("communication", cdr_sql, cdr_feat_path),
        ("financial",     txn_sql, txn_feat_path),
    ]:
        try:
            con.execute(sql)
            size = os.path.getsize(out_path)
            results[name] = {"status": "OK", "path": out_path, "bytes": size}
        except Exception as e:
            results[name] = {"status": "ERROR", "error": str(e)}

    con.close()
    return results

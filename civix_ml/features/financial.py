"""
Financial Features — built entirely via DuckDB SQL.
Aggregates 18M transaction rows per-person without loading into RAM.
Transactions are hive-partitioned: transactions/year=X/month=Y/*.parquet
All features are point-in-time safe via `as_of_timestamp`.
"""
import pandas as pd
from pathlib import Path
from civix_ml.config import PROFILE_C_DIR
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection

log = get_logger(__name__)

# Hive-partitioned glob — transactions use year/month partitions like CDRs
TXN_HIVE_GLOB = str(PROFILE_C_DIR / "transactions" / "**" / "*.parquet").replace("\\", "/")


def build_financial_features(
    as_of_timestamp: str,
    output_path: Path,
    con=None,
) -> pd.DataFrame:
    """
    Build person-level financial features from hive-partitioned transaction Parquet.
    sender_person_id is available directly in the transactions table (no account JOIN needed).
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    log.info(f"Building financial features as_of={as_of_timestamp} ...")
    log.info(f"  TXN source: {TXN_HIVE_GLOB}")

    txn_path = TXN_HIVE_GLOB

    # Pass 1: main per-person aggregates
    pass1_sql = f"""
    WITH txns AS (
        SELECT
            sender_person_id                                          AS person_id,
            amount,
            receiver_account_id,
            transaction_type,
            timestamp,
            CAST(timestamp AS DATE)                                   AS txn_date,
            CAST(SUBSTR(timestamp, 12, 2) AS INTEGER)                 AS txn_hour
        FROM read_parquet('{txn_path}', union_by_name=True, hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND sender_person_id IS NOT NULL
    ),
    p95 AS (
        SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY amount) AS threshold
        FROM txns
    )
    SELECT
        person_id,
        COUNT(*)                                                       AS total_txns,
        COUNT(DISTINCT txn_date)                                       AS active_txn_days,
        COUNT(DISTINCT receiver_account_id)                            AS unique_counterparties,
        COUNT(DISTINCT transaction_type)                               AS txn_type_diversity,
        SUM(amount)                                                    AS total_sent_amount,
        AVG(amount)                                                    AS avg_txn_amount,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY amount)           AS median_txn_amount,
        MAX(amount)                                                    AS max_txn_amount,
        MIN(amount)                                                    AS min_txn_amount,
        STDDEV(amount)                                                 AS std_txn_amount,
        CASE WHEN COUNT(DISTINCT txn_date) > 0
             THEN COUNT(*) * 1.0 / COUNT(DISTINCT txn_date)
             ELSE 0 END                                                AS txns_per_active_day,
        SUM(CASE WHEN amount > (SELECT threshold FROM p95) THEN 1 ELSE 0 END)
                                                                       AS high_value_txn_count,
        AVG(CASE WHEN amount > (SELECT threshold FROM p95) THEN 1.0 ELSE 0.0 END)
                                                                       AS high_value_txn_ratio,
        MIN(timestamp)                                                 AS first_txn_ts,
        MAX(timestamp)                                                 AS last_txn_ts,
        AVG(CASE WHEN txn_hour >= 22 OR txn_hour < 6 THEN 1.0 ELSE 0.0 END)
                                                                       AS night_txn_ratio
    FROM txns
    GROUP BY person_id
    """

    log.info("  Pass 1: main financial aggregates ...")
    df_main = con.execute(pass1_sql).df()
    log.info(f"  Pass 1 done: {len(df_main):,} persons")

    # Pass 2: amount concentration — top counterparty amount / total sent
    pass2_sql = f"""
    WITH txns AS (
        SELECT sender_person_id AS person_id, receiver_account_id, amount
        FROM read_parquet('{txn_path}', union_by_name=True, hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND sender_person_id IS NOT NULL
    ),
    per_cp AS (
        SELECT person_id, receiver_account_id, SUM(amount) AS cp_amount
        FROM txns GROUP BY person_id, receiver_account_id
    ),
    top_cp AS (
        SELECT person_id, MAX(cp_amount) AS max_cp_amount
        FROM per_cp GROUP BY person_id
    ),
    total_sent AS (
        SELECT person_id, SUM(amount) AS total
        FROM txns GROUP BY person_id
    )
    SELECT
        tc.person_id,
        CASE WHEN ts.total > 0
             THEN tc.max_cp_amount / ts.total
             ELSE NULL END                                             AS amount_concentration
    FROM top_cp tc
    JOIN total_sent ts USING (person_id)
    """

    log.info("  Pass 2: amount concentration ...")
    df_conc = con.execute(pass2_sql).df()
    log.info(f"  Pass 2 done: {len(df_conc):,} persons")

    df = df_main.merge(df_conc, on="person_id", how="left")
    log.info(f"  Merged: {len(df):,} persons × {len(df.columns)} fin features")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), index=False, compression="snappy")
    log.info(f"  Saved to {output_path}")

    if close_con:
        con.close()
    return df

"""
Behavioral Features — combines communication + financial + temporal signals.
Detects synchronized activity patterns, burst correlations, and deviations.
Built from already-computed feature Parquet files (not raw CDRs/txns).
"""
import duckdb
import pandas as pd
from pathlib import Path
from civix_ml.utils import get_logger

log = get_logger(__name__)


def build_behavioral_features(
    comm_path: Path,
    fin_path: Path,
    output_path: Path,
) -> pd.DataFrame:
    """
    Derive cross-domain behavioral features by joining communication
    and financial feature tables.

    Parameters
    ----------
    comm_path   : Path to communication features Parquet.
    fin_path    : Path to financial features Parquet.
    output_path : Output path for behavioral features Parquet.
    """
    log.info("Building behavioral features from communication + financial features ...")

    con = duckdb.connect(":memory:")

    comm = str(comm_path).replace("\\", "/")
    fin  = str(fin_path).replace("\\", "/")

    sql = f"""
    WITH c AS (
        SELECT * FROM read_parquet('{comm}')
    ),
    f AS (
        SELECT * FROM read_parquet('{fin}')
    )
    SELECT
        c.person_id,

        -- Synchronized activity: days with both calls AND transactions
        -- (proxy: compare active_days vs active_txn_days)
        ABS(COALESCE(c.active_days, 0) - COALESCE(f.active_txn_days, 0))
            AS active_day_delta,

        -- Communication-to-financial ratio (how many calls per transaction?)
        CASE WHEN COALESCE(f.total_txns, 0) > 0
             THEN c.total_calls * 1.0 / f.total_txns
             ELSE NULL END                                    AS calls_per_txn,

        -- High financial + high communication (volume-driven pattern)
        CASE WHEN c.total_calls > 0 AND f.total_txns > 0
             THEN 1 ELSE 0 END                                AS has_both_activity,

        -- Night activity: both high-night calls AND high-night transactions
        COALESCE(c.night_call_ratio, 0) * COALESCE(f.night_txn_ratio, 0)
            AS night_activity_product,

        -- Burst signal: high std_duration + high std_amount (erratic behavior)
        COALESCE(c.std_duration_sec, 0) / NULLIF(c.avg_duration_sec, 0)
            AS call_duration_cv,   -- coefficient of variation

        COALESCE(f.std_txn_amount, 0) / NULLIF(f.avg_txn_amount, 0)
            AS txn_amount_cv,      -- coefficient of variation

        -- Geographic-communication coherence
        -- (needs geographic features — handled in pipeline)

        -- Activity span in days (communication)
        CASE WHEN c.last_call_ts IS NOT NULL AND c.first_call_ts IS NOT NULL
             THEN DATEDIFF('day',
                    CAST(c.first_call_ts AS DATE),
                    CAST(c.last_call_ts  AS DATE)) + 1
             ELSE 0 END                                       AS comm_span_days,

        -- Activity span in days (financial)
        CASE WHEN f.last_txn_ts IS NOT NULL AND f.first_txn_ts IS NOT NULL
             THEN DATEDIFF('day',
                    CAST(f.first_txn_ts AS DATE),
                    CAST(f.last_txn_ts  AS DATE)) + 1
             ELSE 0 END                                       AS txn_span_days,

        -- Contact concentration × amount concentration (dual-concentration)
        COALESCE(c.contact_concentration, 0) * COALESCE(f.amount_concentration, 0)
            AS dual_concentration,

        -- High contact + high counterparty count ratio
        COALESCE(c.unique_contacts, 0) + COALESCE(f.unique_counterparties, 0)
            AS total_network_size

    FROM c
    LEFT JOIN f USING (person_id)
    """

    df = con.execute(sql).df()
    log.info(f"  Done. {len(df):,} persons with behavioral features.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), index=False, compression="snappy")
    log.info(f"  Saved to {output_path}")
    con.close()
    return df

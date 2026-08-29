"""
Communication Features — built entirely via DuckDB SQL.
Aggregates 75M CDR rows per-person without loading into RAM.
All features are point-in-time safe via `as_of_timestamp`.

OOM fix: uses D: drive for temp spill, 4 threads, no correlated subqueries.
"""
import pandas as pd
from pathlib import Path
from civix_ml.config import CDR_GLOB, NIGHT_START_HOUR, NIGHT_END_HOUR
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection

log = get_logger(__name__)


def build_communication_features(
    as_of_timestamp: str,
    output_path: Path,
    con=None,
) -> pd.DataFrame:
    """
    Build person-level communication features from CDR Parquet files.
    Uses two-pass DuckDB aggregation to avoid correlated subqueries.
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    log.info(f"Building communication features as_of={as_of_timestamp} ...")
    cdr_path = CDR_GLOB.replace("\\", "/")

    # Pass 1: main per-person aggregates
    pass1_sql = f"""
    WITH filtered AS (
        SELECT
            caller_person_id                                          AS person_id,
            callee_phone_id,
            cell_sector_id,
            call_type,
            duration_seconds,
            timestamp,
            CAST(timestamp AS DATE)                                   AS cdr_date,
            CAST(SUBSTR(timestamp, 12, 2) AS INTEGER)                 AS hr,
            DAYOFWEEK(CAST(timestamp AS TIMESTAMP))                   AS dow
        FROM read_parquet('{cdr_path}', union_by_name=True, hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND caller_person_id IS NOT NULL
    )
    SELECT
        person_id,
        COUNT(*)                                                       AS total_calls,
        COUNT(DISTINCT cdr_date)                                       AS active_days,
        COUNT(DISTINCT callee_phone_id)                                AS unique_contacts,
        COUNT(DISTINCT cell_sector_id)                                 AS unique_cell_sectors,
        SUM(CASE WHEN call_type='VOICE' THEN 1 ELSE 0 END)            AS voice_calls,
        SUM(CASE WHEN call_type='SMS'   THEN 1 ELSE 0 END)            AS sms_count,
        SUM(CASE WHEN call_type='DATA'  THEN 1 ELSE 0 END)            AS data_sessions,
        AVG(duration_seconds)                                          AS avg_duration_sec,
        STDDEV(duration_seconds)                                       AS std_duration_sec,
        MAX(duration_seconds)                                          AS max_duration_sec,
        MIN(duration_seconds)                                          AS min_duration_sec,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY duration_seconds) AS median_duration_sec,
        AVG(CASE WHEN duration_seconds < 30  THEN 1.0 ELSE 0.0 END)   AS short_call_ratio,
        AVG(CASE WHEN duration_seconds > 300 THEN 1.0 ELSE 0.0 END)   AS long_call_ratio,
        SUM(CASE WHEN hr >= {NIGHT_START_HOUR} OR hr < {NIGHT_END_HOUR}
                 THEN 1 ELSE 0 END)                                    AS night_call_count,
        AVG(CASE WHEN hr >= {NIGHT_START_HOUR} OR hr < {NIGHT_END_HOUR}
                 THEN 1.0 ELSE 0.0 END)                                AS night_call_ratio,
        AVG(CASE WHEN dow IN (0, 6) THEN 1.0 ELSE 0.0 END)            AS weekend_call_ratio,
        MIN(timestamp)                                                 AS first_call_ts,
        MAX(timestamp)                                                 AS last_call_ts,
        CASE WHEN COUNT(DISTINCT cdr_date) > 0
             THEN COUNT(*) * 1.0 / COUNT(DISTINCT cdr_date)
             ELSE 0 END                                                AS calls_per_active_day
    FROM filtered
    GROUP BY person_id
    """

    log.info("  Pass 1: main aggregates (~30-60s for 75M CDRs) ...")
    df_main = con.execute(pass1_sql).df()
    log.info(f"  Pass 1 done: {len(df_main):,} persons")

    # Pass 2: contact concentration — top-contact calls / total calls
    # No correlated subquery — pre-aggregate then join
    pass2_sql = f"""
    WITH filtered AS (
        SELECT caller_person_id AS person_id, callee_phone_id
        FROM read_parquet('{cdr_path}', union_by_name=True, hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND caller_person_id IS NOT NULL
    ),
    per_contact AS (
        SELECT person_id, callee_phone_id, COUNT(*) AS cnt
        FROM filtered GROUP BY person_id, callee_phone_id
    ),
    top_contact AS (
        SELECT person_id, MAX(cnt) AS max_contact_calls
        FROM per_contact GROUP BY person_id
    ),
    total_calls AS (
        SELECT person_id, SUM(cnt) AS total
        FROM per_contact GROUP BY person_id
    )
    SELECT
        tc.person_id,
        CASE WHEN tot.total > 0
             THEN tc.max_contact_calls * 1.0 / tot.total
             ELSE NULL END AS contact_concentration
    FROM top_contact tc
    JOIN total_calls tot USING (person_id)
    """

    log.info("  Pass 2: contact concentration ...")
    df_conc = con.execute(pass2_sql).df()
    log.info(f"  Pass 2 done: {len(df_conc):,} persons")

    # Merge
    df = df_main.merge(df_conc, on="person_id", how="left")
    log.info(f"  Merged: {len(df):,} persons × {len(df.columns)} comm features")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(str(output_path), index=False, compression="snappy")
    log.info(f"  Saved to {output_path}")

    if close_con:
        con.close()
    return df

"""
CIVIX CDR Graph Construction — Phase 3B
Builds phone→phone temporal edges from 75M CDR records.
Processing is entirely out-of-core using DuckDB + Parquet.

Two representations are produced:
  1. Temporal edges (raw events, partitioned by year/month)
  2. Aggregated edges (one row per unique phone pair)
"""
import json
import pyarrow as pa
import pyarrow.parquet as pq
from pathlib import Path
from datetime import datetime

from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.graph.schema import GRAPH_EDGES_DIR, GRAPH_META_DIR

log = get_logger(__name__)

CDR_GLOB       = config.CDR_GLOB.replace("\\", "/")
TEMPORAL_DIR   = GRAPH_EDGES_DIR / "cdr_temporal"
AGGREGATED_DIR = GRAPH_EDGES_DIR / "cdr_aggregated"


def build_cdr_temporal_edges(as_of_timestamp: str = config.DEFAULT_AS_OF,
                              force: bool = False) -> Path:
    """
    Extract raw temporal CDR edges, filtered by as_of_timestamp.
    Partitioned by year/month to avoid RAM exhaustion.
    Columns: caller_phone_id, callee_phone_id, timestamp, duration_seconds, call_type, cell_sector_id
    """
    out_path = TEMPORAL_DIR
    sentinel = TEMPORAL_DIR / "_SUCCESS"
    if sentinel.exists() and not force:
        log.info(f"  [skip] CDR temporal edges already exist at {out_path}")
        return out_path
    out_path.mkdir(parents=True, exist_ok=True)

    con = get_connection()
    log.info(f"Building CDR temporal edges as_of={as_of_timestamp} ...")

    # Get distinct years to partition
    years = con.execute(f"""
        SELECT DISTINCT year FROM read_parquet('{CDR_GLOB}', hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
        ORDER BY year
    """).df()["year"].tolist()

    total_edges = 0
    for yr in years:
        months = con.execute(f"""
            SELECT DISTINCT month FROM read_parquet('{CDR_GLOB}', hive_partitioning=True)
            WHERE year = {yr} AND timestamp <= '{as_of_timestamp}'
            ORDER BY month
        """).df()["month"].tolist()

        for mo in months:
            part_dir = out_path / f"year={yr}" / f"month={mo}"
            part_dir.mkdir(parents=True, exist_ok=True)
            part_file = part_dir / "edges.parquet"

            chunk_df = con.execute(f"""
                SELECT
                    caller_phone_id,
                    callee_phone_id,
                    timestamp,
                    duration_seconds,
                    call_type,
                    cell_sector_id
                FROM read_parquet('{CDR_GLOB}', hive_partitioning=True)
                WHERE year = {yr} AND month = {mo}
                  AND timestamp <= '{as_of_timestamp}'
                  AND caller_phone_id IS NOT NULL
                  AND callee_phone_id IS NOT NULL
            """).df()

            pq.write_table(
                pa.Table.from_pandas(chunk_df, preserve_index=False),
                str(part_file)
            )
            total_edges += len(chunk_df)
            log.info(f"  CDR temporal: year={yr} month={mo:02d} → {len(chunk_df):,} edges")

    sentinel.write_text(f"generated={datetime.utcnow().isoformat()} total_edges={total_edges}")
    log.info(f"  CDR temporal edges complete: {total_edges:,} total")
    con.close()
    return out_path


def build_cdr_aggregated_edges(as_of_timestamp: str = config.DEFAULT_AS_OF,
                                force: bool = False) -> Path:
    """
    Aggregate CDRs into one row per unique (caller_phone_id, callee_phone_id) pair.
    Captures: call_count, total_duration, first_contact, last_contact, active_days, is_reciprocal
    This is the static relationship graph — distinct from the event graph.
    """
    out_file = AGGREGATED_DIR / "cdr_aggregated.parquet"
    AGGREGATED_DIR.mkdir(parents=True, exist_ok=True)
    if out_file.exists() and not force:
        log.info(f"  [skip] CDR aggregated edges already exist at {out_file}")
        return out_file

    con = get_connection()
    log.info(f"Building CDR aggregated edges as_of={as_of_timestamp} ...")

    sql = f"""
    WITH raw AS (
        SELECT
            caller_phone_id   AS src,
            callee_phone_id   AS dst,
            duration_seconds,
            CAST(timestamp AS TIMESTAMP) AS ts
        FROM read_parquet('{CDR_GLOB}', hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND caller_phone_id IS NOT NULL
          AND callee_phone_id IS NOT NULL
    ),
    agg AS (
        SELECT
            src,
            dst,
            COUNT(*)                                                 AS call_count,
            SUM(duration_seconds)                                    AS total_duration_sec,
            AVG(duration_seconds)                                    AS avg_duration_sec,
            MIN(ts)                                                  AS first_contact,
            MAX(ts)                                                  AS last_contact,
            COUNT(DISTINCT CAST(ts AS DATE))                         AS active_days
        FROM raw
        GROUP BY src, dst
    ),
    -- Check reciprocity: does the reverse edge also exist?
    recip AS (
        SELECT src AS rsrc, dst AS rdst FROM agg
    )
    SELECT
        a.src,
        a.dst,
        a.call_count,
        a.total_duration_sec,
        a.avg_duration_sec,
        a.first_contact,
        a.last_contact,
        a.active_days,
        CASE WHEN r.rsrc IS NOT NULL THEN 1 ELSE 0 END AS is_reciprocal
    FROM agg a
    LEFT JOIN recip r ON r.rsrc = a.dst AND r.rdst = a.src
    """

    df = con.execute(sql).df()
    log.info(f"  CDR aggregated: {len(df):,} unique phone pairs")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), str(out_file))

    # Write metadata
    meta = {
        "as_of_timestamp": as_of_timestamp,
        "unique_pairs":    len(df),
        "total_calls":     int(df["call_count"].sum()),
        "max_calls_on_edge": int(df["call_count"].max()),
    }
    (GRAPH_META_DIR / "cdr_aggregated_meta.json").write_text(json.dumps(meta, indent=2))
    log.info(f"  Saved → {out_file}")
    con.close()
    return out_file

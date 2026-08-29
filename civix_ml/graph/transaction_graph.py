"""
CIVIX Transaction Graph Construction — Phase 3B
Builds account→account financial edges from ~18M transaction records.
Out-of-core via DuckDB. Produces both raw temporal and aggregated edge lists.
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

TXN_GLOB       = config.TXN_GLOB.replace("\\", "/")
TXN_AGG_DIR    = GRAPH_EDGES_DIR / "txn_aggregated"


def build_txn_aggregated_edges(as_of_timestamp: str = config.DEFAULT_AS_OF,
                                force: bool = False) -> Path:
    """
    Aggregate transactions into one row per (sender_account_id, receiver_account_id).
    Also includes person-level mapping via sender_person_id.
    """
    TXN_AGG_DIR.mkdir(parents=True, exist_ok=True)
    out_file = TXN_AGG_DIR / "txn_aggregated.parquet"
    if out_file.exists() and not force:
        log.info(f"  [skip] Transaction aggregated edges already exist at {out_file}")
        return out_file

    con = get_connection()
    log.info(f"Building transaction aggregated edges as_of={as_of_timestamp} ...")

    sql = f"""
    WITH raw AS (
        SELECT
            sender_account_id,
            receiver_account_id,
            sender_person_id,
            amount,
            transaction_type,
            CAST(timestamp AS TIMESTAMP) AS ts
        FROM read_parquet('{TXN_GLOB}', union_by_name=True, hive_partitioning=True)
        WHERE timestamp <= '{as_of_timestamp}'
          AND sender_account_id  IS NOT NULL
          AND receiver_account_id IS NOT NULL
    ),
    agg AS (
        SELECT
            sender_account_id   AS src,
            receiver_account_id AS dst,
            sender_person_id,
            COUNT(*)                                          AS txn_count,
            SUM(amount)                                       AS total_amount,
            AVG(amount)                                       AS avg_amount,
            MAX(amount)                                       AS max_amount,
            MIN(ts)                                           AS first_txn,
            MAX(ts)                                           AS last_txn,
            COUNT(DISTINCT CAST(ts AS DATE))                  AS active_days,
            COUNT(DISTINCT transaction_type)                  AS txn_type_count
        FROM raw
        GROUP BY sender_account_id, receiver_account_id, sender_person_id
    )
    SELECT * FROM agg
    """

    df = con.execute(sql).df()
    log.info(f"  Txn aggregated: {len(df):,} unique account pairs")
    pq.write_table(pa.Table.from_pandas(df, preserve_index=False), str(out_file))

    meta = {
        "as_of_timestamp":   as_of_timestamp,
        "unique_pairs":      len(df),
        "total_transactions": int(df["txn_count"].sum()),
    }
    (GRAPH_META_DIR / "txn_aggregated_meta.json").write_text(json.dumps(meta, indent=2))
    log.info(f"  Saved → {out_file}")
    con.close()
    return out_file

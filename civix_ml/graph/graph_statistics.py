"""
CIVIX Graph Statistics — Phase 3B
Computes summary statistics of the graph for the synthetic artifact audit.
All statistics are computed out-of-core via DuckDB.
"""
import json
import pandas as pd
import numpy as np
from pathlib import Path
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.graph.schema import GRAPH_EDGES_DIR, GRAPH_META_DIR
from civix_ml import config

log = get_logger(__name__)

CDR_AGG  = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet").replace("\\", "/")
TXN_AGG  = str(GRAPH_EDGES_DIR / "txn_aggregated" / "txn_aggregated.parquet").replace("\\", "/")
PHONES_GLOB = config.PHONES_GLOB.replace("\\", "/")
LABELS_GLOB = config.LABELS_GLOB.replace("\\", "/")


def compute_graph_statistics() -> dict:
    """
    Compute high-level graph statistics for the GRAPH_DATASET_REPORT.md.
    """
    con = get_connection()
    stats = {}

    log.info("Computing CDR graph statistics ...")
    cdr_stats = con.execute(f"""
        SELECT
            COUNT(*) AS unique_phone_pairs,
            SUM(call_count) AS total_calls,
            AVG(call_count) AS avg_calls_per_pair,
            MAX(call_count) AS max_calls_per_pair,
            SUM(is_reciprocal) AS reciprocal_pairs,
            AVG(CASE WHEN call_count > 0 THEN is_reciprocal * 1.0 ELSE 0 END) AS reciprocity_rate
        FROM read_parquet('{CDR_AGG}')
    """).fetchone()

    stats["cdr_graph"] = {
        "unique_phone_pairs":  cdr_stats[0],
        "total_calls":         cdr_stats[1],
        "avg_calls_per_pair":  round(cdr_stats[2], 2),
        "max_calls_per_pair":  cdr_stats[3],
        "reciprocal_pairs":    cdr_stats[4],
        "reciprocity_rate":    round(cdr_stats[5], 4),
    }

    log.info("Computing person-level degree distribution ...")
    cdr_glob = config.CDR_GLOB.replace("\\", "/")
    degree_sql = f"""
    WITH phones AS (
        SELECT DISTINCT caller_phone_id AS phone_id, caller_person_id AS person_id
        FROM read_parquet('{cdr_glob}')
        WHERE caller_person_id IS NOT NULL
    ),
    out_deg AS (
        SELECT p.person_id, COALESCE(COUNT(c.src), 0) AS out_degree
        FROM phones p
        LEFT JOIN read_parquet('{CDR_AGG}') c ON c.src = p.phone_id
        GROUP BY p.person_id
    )
    SELECT
        MIN(out_degree) AS min_degree,
        MAX(out_degree) AS max_degree,
        AVG(out_degree) AS mean_degree,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY out_degree) AS median_degree,
        STDDEV(out_degree) AS std_degree
    FROM out_deg
    """
    deg_stats = con.execute(degree_sql).fetchone()
    stats["degree_distribution"] = {
        "min": deg_stats[0], "max": deg_stats[1],
        "mean": round(deg_stats[2], 2), "median": deg_stats[3],
        "std": round(deg_stats[4], 2),
    }

    log.info("Computing transaction graph statistics ...")
    txn_stats = con.execute(f"""
        SELECT
            COUNT(*) AS unique_account_pairs,
            SUM(txn_count) AS total_transactions,
            AVG(txn_count) AS avg_txns_per_pair,
            MAX(txn_count) AS max_txns_per_pair
        FROM read_parquet('{TXN_AGG}')
    """).fetchone()
    stats["txn_graph"] = {
        "unique_account_pairs": txn_stats[0],
        "total_transactions":   txn_stats[1],
        "avg_txns_per_pair":    round(txn_stats[2], 2),
        "max_txns_per_pair":    txn_stats[3],
    }

    out_path = GRAPH_META_DIR / "graph_statistics.json"
    out_path.write_text(json.dumps(stats, indent=2, default=str))
    log.info(f"Graph statistics saved → {out_path}")
    con.close()
    return stats


def compute_degree_by_scenario() -> pd.DataFrame:
    """
    Compute per-scenario degree distributions for the synthetic artifact audit.
    This reveals whether the generator hardcoded degree values per scenario.
    """
    con = get_connection()
    log.info("Computing degree distribution by scenario class ...")

    cdr_glob = config.CDR_GLOB.replace("\\", "/")
    sql = f"""
    WITH phones AS (
        SELECT DISTINCT caller_phone_id AS phone_id, caller_person_id AS person_id
        FROM read_parquet('{cdr_glob}')
        WHERE caller_person_id IS NOT NULL
    ),
    labels AS (
        SELECT entity_id AS person_id, scenario_class
        FROM read_parquet('{LABELS_GLOB}')
    ),
    out_deg AS (
        SELECT p.person_id, COALESCE(SUM(c.call_count), 0) AS weighted_out_degree,
               COUNT(DISTINCT c.dst) AS unique_out_contacts
        FROM phones p
        LEFT JOIN read_parquet('{CDR_AGG}') c ON c.src = p.phone_id
        GROUP BY p.person_id
    )
    SELECT
        l.scenario_class,
        COUNT(*) AS n_persons,
        AVG(o.weighted_out_degree) AS mean_out_degree,
        STDDEV(o.weighted_out_degree) AS std_out_degree,
        MIN(o.weighted_out_degree) AS min_out_degree,
        MAX(o.weighted_out_degree) AS max_out_degree,
        AVG(o.unique_out_contacts) AS mean_unique_contacts
    FROM out_deg o
    JOIN labels l ON l.person_id = o.person_id
    GROUP BY l.scenario_class
    ORDER BY l.scenario_class
    """
    df = con.execute(sql).df()
    con.close()
    return df

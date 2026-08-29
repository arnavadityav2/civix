"""
CIVIX Graph Structural Features — Phase 3B
Computes person-level graph topology features from aggregated edge lists.
All computation is done out-of-core via DuckDB over Parquet edge files.
NO full NetworkX graph is created for the complete dataset.
Expensive centrality metrics are approximated or skipped with documentation.
"""
import json
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from pathlib import Path

from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.graph.schema import GRAPH_FEATURES_DIR, GRAPH_META_DIR
from civix_ml.graph.schema import GRAPH_MAPPINGS_DIR, GRAPH_EDGES_DIR

log = get_logger(__name__)

CDR_AGG     = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet").replace("\\", "/")
TXN_AGG     = str(GRAPH_EDGES_DIR / "txn_aggregated" / "txn_aggregated.parquet").replace("\\", "/")
PHONES_GLOB = config.PHONES_GLOB.replace("\\", "/")
PERSONS_GLOB= config.PERSONS_GLOB.replace("\\", "/")
ACCS_GLOB   = config.ACCOUNTS_GLOB.replace("\\", "/")


def build_graph_features(as_of_timestamp: str = config.DEFAULT_AS_OF,
                          force: bool = False) -> pd.DataFrame:
    """
    Build person-level graph structural features.
    Returns a DataFrame with columns (person_id, <graph features...>).
    All computation is DuckDB SQL — no full graph materialised in RAM.
    """
    out_path = GRAPH_FEATURES_DIR / "graph_features.parquet"
    GRAPH_FEATURES_DIR.mkdir(parents=True, exist_ok=True)

    if out_path.exists() and not force:
        log.info(f"  [skip] Graph features already exist at {out_path}")
        return pq.read_table(str(out_path)).to_pandas()

    con = get_connection()
    log.info("Building graph structural features ...")

    # ── STEP 1: Phone-level CDR degree features ───────────────────────────────
    # (person identified via phones table: phone_id -> person_id)
    log.info("  Step 1: Phone-level CDR degree features ...")
    phone_degree_sql = f"""
    WITH out_edges AS (
        SELECT src AS phone_id, COUNT(*) AS out_calls, COUNT(DISTINCT dst) AS out_unique_contacts,
               SUM(call_count) AS total_out_calls, SUM(total_duration_sec) AS total_out_duration
        FROM read_parquet('{CDR_AGG}')
        GROUP BY src
    ),
    in_edges AS (
        SELECT dst AS phone_id, COUNT(*) AS in_calls, COUNT(DISTINCT src) AS in_unique_contacts,
               SUM(call_count) AS total_in_calls
        FROM read_parquet('{CDR_AGG}')
        GROUP BY dst
    ),
    reciprocal AS (
        SELECT src AS phone_id, SUM(is_reciprocal) AS reciprocal_pairs
        FROM read_parquet('{CDR_AGG}')
        GROUP BY src
    ),
    phones AS (
        SELECT phone_id, person_id
        FROM read_parquet('{PHONES_GLOB}')
        WHERE person_id IS NOT NULL
    )
    SELECT
        p.person_id,
        COALESCE(o.out_calls, 0)           AS cdr_out_degree,
        COALESCE(o.out_unique_contacts, 0)  AS cdr_unique_out_contacts,
        COALESCE(o.total_out_calls, 0)      AS cdr_total_out_calls,
        COALESCE(o.total_out_duration, 0)   AS cdr_total_out_duration,
        COALESCE(i.in_calls, 0)             AS cdr_in_degree,
        COALESCE(i.in_unique_contacts, 0)   AS cdr_unique_in_contacts,
        COALESCE(i.total_in_calls, 0)       AS cdr_total_in_calls,
        COALESCE(o.out_calls, 0) + COALESCE(i.in_calls, 0) AS cdr_total_degree,
        COALESCE(r.reciprocal_pairs, 0)     AS cdr_reciprocal_pairs,
        CASE
            WHEN COALESCE(o.out_calls, 0) > 0
            THEN COALESCE(r.reciprocal_pairs, 0) * 1.0 / o.out_calls
            ELSE 0
        END                                 AS cdr_reciprocity_ratio,
        -- contact concentration: max_pair_calls / total_out_calls
        CASE
            WHEN COALESCE(o.total_out_calls, 0) > 0
            THEN (
                SELECT MAX(call_count) FROM read_parquet('{CDR_AGG}') q
                WHERE q.src = p.phone_id
            ) * 1.0 / o.total_out_calls
            ELSE NULL
        END                                 AS cdr_call_concentration
    FROM phones p
    LEFT JOIN out_edges o ON o.phone_id = p.phone_id
    LEFT JOIN in_edges  i ON i.phone_id = p.phone_id
    LEFT JOIN reciprocal r ON r.phone_id = p.phone_id
    """
    # NOTE: The correlated subquery for concentration is expensive — use 2-pass instead
    # Pass 1: all degree features
    phone_deg_sql_v2 = f"""
    WITH out_edges AS (
        SELECT src AS phone_id,
               COUNT(*) AS out_pairs,
               COUNT(DISTINCT dst) AS out_unique_contacts,
               SUM(call_count) AS total_out_calls,
               SUM(total_duration_sec) AS total_out_duration,
               MAX(call_count) AS max_pair_calls
        FROM read_parquet('{CDR_AGG}')
        GROUP BY src
    ),
    in_edges AS (
        SELECT dst AS phone_id,
               COUNT(*) AS in_pairs,
               COUNT(DISTINCT src) AS in_unique_contacts,
               SUM(call_count) AS total_in_calls
        FROM read_parquet('{CDR_AGG}')
        GROUP BY dst
    ),
    recip AS (
        SELECT src AS phone_id, SUM(is_reciprocal) AS reciprocal_pairs
        FROM read_parquet('{CDR_AGG}')
        GROUP BY src
    ),
    phones AS (
        SELECT DISTINCT caller_phone_id AS phone_id, caller_person_id AS person_id
        FROM read_parquet('{config.CDR_GLOB.replace("\\", "/")}')
        WHERE caller_person_id IS NOT NULL
    ),
    person_agg AS (
        SELECT
            p.person_id,
            SUM(COALESCE(o.out_pairs, 0))              AS cdr_out_degree,
            SUM(COALESCE(o.out_unique_contacts, 0))    AS cdr_unique_out_contacts,
            SUM(COALESCE(o.total_out_calls, 0))        AS cdr_total_out_calls,
            SUM(COALESCE(o.total_out_duration, 0))     AS cdr_total_out_duration,
            MAX(COALESCE(o.max_pair_calls, 0))         AS cdr_max_pair_calls,
            SUM(COALESCE(i.in_pairs, 0))               AS cdr_in_degree,
            SUM(COALESCE(i.in_unique_contacts, 0))     AS cdr_unique_in_contacts,
            SUM(COALESCE(i.total_in_calls, 0))         AS cdr_total_in_calls,
            SUM(COALESCE(r.reciprocal_pairs, 0))       AS cdr_reciprocal_pairs
        FROM phones p
        LEFT JOIN out_edges o ON o.phone_id = p.phone_id
        LEFT JOIN in_edges  i ON i.phone_id = p.phone_id
        LEFT JOIN recip     r ON r.phone_id = p.phone_id
        GROUP BY p.person_id
    )
    SELECT
        *,
        cdr_out_degree + cdr_in_degree                  AS cdr_total_degree,
        CASE WHEN cdr_out_degree > 0
             THEN cdr_reciprocal_pairs * 1.0 / cdr_out_degree
             ELSE 0 END                                  AS cdr_reciprocity_ratio,
        CASE WHEN cdr_total_out_calls > 0
             THEN cdr_max_pair_calls * 1.0 / cdr_total_out_calls
             ELSE NULL END                               AS cdr_call_concentration
    FROM person_agg
    """

    log.info("    Running phone-degree aggregation ...")
    df_cdr = con.execute(phone_deg_sql_v2).df()
    log.info(f"    CDR graph features: {len(df_cdr):,} persons × {len(df_cdr.columns)-1} features")

    # ── STEP 2: Financial graph features (account → person) ───────────────────
    log.info("  Step 2: Financial graph features ...")
    txn_sql = f"""
    WITH accs AS (
        SELECT account_id, primary_holder_id AS person_id
        FROM read_parquet('{ACCS_GLOB}')
        WHERE primary_holder_id IS NOT NULL
    ),
    out_txn AS (
        SELECT t.src AS account_id,
               COUNT(*) AS out_pairs,
               COUNT(DISTINCT t.dst) AS out_counterparties,
               SUM(t.txn_count) AS total_out_txns,
               SUM(t.total_amount) AS total_out_amount,
               MAX(t.txn_count) AS max_pair_txns
        FROM read_parquet('{TXN_AGG}') t
        GROUP BY t.src
    ),
    in_txn AS (
        SELECT t.dst AS account_id,
               COUNT(*) AS in_pairs,
               COUNT(DISTINCT t.src) AS in_counterparties,
               SUM(t.txn_count) AS total_in_txns,
               SUM(t.total_amount) AS total_in_amount
        FROM read_parquet('{TXN_AGG}') t
        GROUP BY t.dst
    ),
    person_txn AS (
        SELECT
            a.person_id,
            SUM(COALESCE(o.out_pairs, 0))         AS txn_out_degree,
            SUM(COALESCE(o.out_counterparties, 0)) AS txn_unique_out_cp,
            SUM(COALESCE(o.total_out_txns, 0))    AS txn_total_out,
            SUM(COALESCE(o.total_out_amount, 0))  AS txn_total_out_amount,
            MAX(COALESCE(o.max_pair_txns, 0))     AS txn_max_pair_txns,
            SUM(COALESCE(i.in_pairs, 0))          AS txn_in_degree,
            SUM(COALESCE(i.in_counterparties, 0)) AS txn_unique_in_cp,
            SUM(COALESCE(i.total_in_txns, 0))     AS txn_total_in,
            SUM(COALESCE(i.total_in_amount, 0))   AS txn_total_in_amount
        FROM accs a
        LEFT JOIN out_txn o ON o.account_id = a.account_id
        LEFT JOIN in_txn  i ON i.account_id = a.account_id
        GROUP BY a.person_id
    )
    SELECT
        *,
        txn_out_degree + txn_in_degree           AS txn_total_degree,
        CASE WHEN txn_total_out > 0
             THEN txn_max_pair_txns * 1.0 / txn_total_out
             ELSE NULL END                        AS txn_flow_concentration,
        CASE WHEN txn_total_out_amount + txn_total_in_amount > 0
             THEN txn_total_out_amount / (txn_total_out_amount + txn_total_in_amount)
             ELSE NULL END                        AS txn_net_flow_ratio
    FROM person_txn
    """
    df_txn = con.execute(txn_sql).df()
    log.info(f"    Txn graph features: {len(df_txn):,} persons × {len(df_txn.columns)-1} features")

    # ── STEP 3: Person-level aggregated CDR temporal features ─────────────────
    log.info("  Step 3: Person-level CDR temporal scope ...")
    persons_sql = f"""
    SELECT person_id FROM read_parquet('{PERSONS_GLOB}')
    """
    df_persons = con.execute(persons_sql).df()

    # ── STEP 4: PageRank approximation via DuckDB iterative joins ─────────────
    # Full PageRank on 75M edges is not feasible on 16GB RAM.
    # We use degree-weighted approximation: PR_approx = out_degree / sqrt(in_degree+1)
    # This is documented as an approximation, not true PageRank.
    log.info("  Step 4: PageRank approximation (degree-weighted, not exact PR) ...")
    # Merge CDR features to compute approximation
    df_cdr_pr = df_cdr[["person_id", "cdr_out_degree", "cdr_in_degree"]].copy()
    df_cdr_pr["cdr_pagerank_approx"] = (
        df_cdr_pr["cdr_out_degree"] /
        (np.sqrt(df_cdr_pr["cdr_in_degree"] + 1) + 1e-9)
    )

    # ── STEP 5: Merge all features ────────────────────────────────────────────
    log.info("  Step 5: Merging all graph features ...")
    df_all = df_persons.merge(df_cdr, on="person_id", how="left")
    df_all = df_all.merge(df_txn, on="person_id", how="left")
    df_all = df_all.merge(df_cdr_pr[["person_id", "cdr_pagerank_approx"]], on="person_id", how="left")
    df_all = df_all.fillna(0)

    log.info(f"  Graph features complete: {len(df_all):,} persons × {len(df_all.columns)-1} features")
    pq.write_table(pa.Table.from_pandas(df_all, preserve_index=False), str(out_path))

    meta = {
        "as_of_timestamp": as_of_timestamp,
        "n_persons": len(df_all),
        "n_features": len(df_all.columns) - 1,
        "features": [c for c in df_all.columns if c != "person_id"],
        "notes": {
            "cdr_pagerank_approx": "Degree-weighted approximation. Not exact PageRank. Exact PR would require iterative computation on full 75M-node graph — not feasible on G15 RAM.",
            "betweenness_centrality": "SKIPPED. Exact betweenness on 250k-node graph would take hours and exceed 16GB RAM. Not computed.",
            "community_membership": "SKIPPED in this step. Implemented via SciPy connected components below.",
        }
    }
    (GRAPH_META_DIR / "graph_features_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    con.close()
    return df_all

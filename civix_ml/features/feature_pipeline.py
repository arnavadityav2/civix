"""
Feature Pipeline Orchestrator.
Runs all feature builders in sequence, saves per-feature Parquet files,
then merges them into a single person-level feature matrix.
Also joins ground truth labels for training.
"""
import duckdb
import pandas as pd
from pathlib import Path
from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.duckdb_utils import get_connection
from civix_ml.features.communication import build_communication_features
from civix_ml.features.financial    import build_financial_features
from civix_ml.features.geographic   import build_geographic_features
from civix_ml.features.behavioral   import build_behavioral_features

log = get_logger(__name__)

# ── Leakage guard: columns that MUST NOT appear in any feature table ─────────
FORBIDDEN_COLUMNS = {
    "scenario_class", "scenario_family", "scenario_id_str", "scenario_category",
    "is_positive_label", "is_false_positive", "risk_score_gt", "ground_truth_note",
    "risk_score",   # from persons table (derived from ground truth)
    "financial_pattern", # scenario mechanism label from transactions
}


def run_feature_pipeline(
    as_of_timestamp: str = config.DEFAULT_AS_OF,
    output_dir: Path = config.FEATURES_DIR,
    skip_existing: bool = True,
) -> Path:
    """
    Build all features for Profile C and produce a merged feature matrix.

    Returns
    -------
    Path to the final merged Parquet file.
    """
    log.info("=" * 60)
    log.info("CIVIX Feature Pipeline")
    log.info(f"  as_of_timestamp : {as_of_timestamp}")
    log.info(f"  output_dir      : {output_dir}")
    log.info("=" * 60)

    output_dir.mkdir(parents=True, exist_ok=True)
    con = get_connection()

    # ── 1. Communication features ────────────────────────────────────────────
    comm_path = output_dir / "comm_features.parquet"
    if not skip_existing or not comm_path.exists():
        build_communication_features(as_of_timestamp, comm_path, con=con)
    else:
        log.info(f"  [skip] communication features already exist at {comm_path}")

    # ── 2. Financial features ────────────────────────────────────────────────
    fin_path = output_dir / "fin_features.parquet"
    if not skip_existing or not fin_path.exists():
        build_financial_features(as_of_timestamp, fin_path, con=con)
    else:
        log.info(f"  [skip] financial features already exist at {fin_path}")

    # ── 3. Geographic features ───────────────────────────────────────────────
    geo_path = output_dir / "geo_features.parquet"
    if not skip_existing or not geo_path.exists():
        build_geographic_features(as_of_timestamp, geo_path, con=con)
    else:
        log.info(f"  [skip] geographic features already exist at {geo_path}")

    # ── 4. Behavioral features ───────────────────────────────────────────────
    beh_path = output_dir / "beh_features.parquet"
    if not skip_existing or not beh_path.exists():
        build_behavioral_features(comm_path, fin_path, beh_path)
    else:
        log.info(f"  [skip] behavioral features already exist at {beh_path}")

    # ── 5. Merge all feature tables ──────────────────────────────────────────
    merged_path = output_dir / "features_merged.parquet"
    log.info("Merging all feature tables ...")

    comm = str(comm_path).replace("\\", "/")
    fin  = str(fin_path).replace("\\", "/")
    geo  = str(geo_path).replace("\\", "/")
    beh  = str(beh_path).replace("\\", "/")
    persons = config.PERSONS_GLOB.replace("\\", "/")

    merge_sql = f"""
    WITH persons AS (
        SELECT person_id, gender, occupation
        FROM read_parquet('{persons}')
    ),
    c AS (SELECT * FROM read_parquet('{comm}')),
    f AS (SELECT * EXCLUDE(person_id) FROM read_parquet('{fin}')),
    g AS (SELECT * EXCLUDE(person_id) FROM read_parquet('{geo}')),
    b AS (SELECT * EXCLUDE(person_id) FROM read_parquet('{beh}'))
    SELECT
        p.person_id,
        p.gender,
        p.occupation,
        c.* EXCLUDE(person_id),
        f.*,
        g.*,
        b.*
    FROM persons p
    LEFT JOIN c  USING (person_id)
    LEFT JOIN f  ON c.person_id = f.person_id   -- bridge via c
    LEFT JOIN g  ON c.person_id = g.person_id
    LEFT JOIN b  ON c.person_id = b.person_id
    """

    # Re-run with simpler join
    merge_sql2 = f"""
    SELECT
        p.person_id,
        p.gender,
        p.occupation,
        c.* EXCLUDE(person_id),
        f.* EXCLUDE(person_id),
        g.* EXCLUDE(person_id),
        b.* EXCLUDE(person_id)
    FROM read_parquet('{persons}') p
    LEFT JOIN read_parquet('{comm}') c USING (person_id)
    LEFT JOIN read_parquet('{fin}')  f USING (person_id)
    LEFT JOIN read_parquet('{geo}')  g USING (person_id)
    LEFT JOIN read_parquet('{beh}')  b USING (person_id)
    """

    df = con.execute(merge_sql2).df()
    log.info(f"  Merged: {len(df):,} persons × {len(df.columns)} raw columns")

    # ── 6. Leakage gate ──────────────────────────────────────────────────────
    leaked = [c for c in df.columns if c.lower() in FORBIDDEN_COLUMNS]
    if leaked:
        con.close()
        raise RuntimeError(
            f"GATE FAIL — Leakage detected in feature matrix: {leaked}\n"
            "Do NOT proceed to model training. Fix the feature pipeline."
        )
    log.info("  Leakage gate PASSED — no forbidden columns found.")

    df.to_parquet(str(merged_path), index=False, compression="snappy")
    log.info(f"  Saved merged features to {merged_path}")
    log.info(f"  Final shape: {df.shape}")

    con.close()
    return merged_path


def load_training_data(
    feature_path: Path,
    split: str = "TRAIN",
) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Load feature matrix + labels for a given split.

    Returns (X, y_binary, y_scenario_class)
    y_binary = 1 if confirmed_pattern, else 0
    y_scenario_class = raw scenario class string

    CRITICAL: Ground truth is joined HERE, not stored in features.
    """
    con = get_connection()

    feat  = str(feature_path).replace("\\", "/")
    labs  = config.LABELS_GLOB.replace("\\", "/")
    splits = config.SPLITS_GLOB.replace("\\", "/")

    sql = f"""
    SELECT
        f.*,
        l.scenario_class,
        l.is_positive_label,
        l.is_false_positive,
        l.difficulty
    FROM read_parquet('{feat}')   f
    JOIN read_parquet('{splits}') s ON s.entity_id = f.person_id
    JOIN read_parquet('{labs}')   l ON l.entity_id = f.person_id
    WHERE s.split = '{split}'
    """

    df = con.execute(sql).df()
    con.close()

    # Separate label columns — NEVER pass these to the model
    label_cols = ["scenario_class", "is_positive_label", "is_false_positive", "difficulty"]
    y_binary   = df["is_positive_label"].astype(int)
    y_scenario = df["scenario_class"]
    y_fp       = df["is_false_positive"]

    # Drop ALL non-feature columns (including raw timestamps — they're artifacts)
    RAW_TS_COLS = ["first_call_ts", "last_call_ts", "first_txn_ts", "last_txn_ts"]
    drop_cols = ["person_id"] + label_cols + RAW_TS_COLS + config.GENERATOR_ARTIFACT_FEATURES
    X = df.drop(columns=drop_cols, errors="ignore")

    # Log exactly which artifact features were dropped
    dropped_artifacts = [c for c in config.GENERATOR_ARTIFACT_FEATURES if c in df.columns]
    if dropped_artifacts:
        log.info(f"  [GATE4] Dropped {len(dropped_artifacts)} generator-artifact features: {dropped_artifacts}")

    # One-hot encode ONLY low-cardinality categoricals (< 50 unique values)
    # This prevents explosion from any near-unique string columns
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    safe_cat = [c for c in cat_cols if X[c].nunique() < 50]
    high_card = [c for c in cat_cols if c not in safe_cat]
    if high_card:
        log.warning(f"  Dropping high-cardinality string columns: {high_card}")
        X = X.drop(columns=high_card)
    if safe_cat:
        X = pd.get_dummies(X, columns=safe_cat, drop_first=True, dtype=float)

    # Fill NaN with 0 (persons with no CDRs or no transactions)
    X = X.fillna(0)

    log.info(f"  Loaded split={split}: {len(X):,} persons, {X.shape[1]} features")
    return X, y_binary, y_scenario

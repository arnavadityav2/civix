"""
CIVIX ML Pipeline — Unified CLI entry point.
Usage: python -m civix_ml <command> [options]

Phase 3A Commands:
  features build   — Build all behavioral feature tables from Profile C
  features audit   — Audit features for leakage + statistics
  train            — Train a Phase 3A baseline model
  evaluate         — Evaluate Phase 3A models on test set
  adversarial      — Run Phase 3A adversarial tests

Phase 3B Commands:
  graph build      — Build CDR + transaction graph edge lists
  graph stats      — Compute graph statistics (degree, reciprocity, etc.)
  graph features   — Compute person-level graph structural features
  graph validate   — Validate temporal and label leakage in graph
  graph baseline   — Train graph-only baselines
  graph compare    — Three-way comparison: behavioral vs graph vs combined
  graph audit      — Synthetic artifact audit on graph features
  gnn train        — Train GraphSAGE GNN
  gnn evaluate     — Evaluate trained GNN on test set
"""
import sys
import json
import time
import pickle
import argparse
import numpy as np
import pandas as pd
from pathlib import Path

from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.reproducibility import set_global_seed

log = get_logger("civix_ml.cli")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND: features build
# ─────────────────────────────────────────────────────────────────────────────
def cmd_features_build(args):
    from civix_ml.features.feature_pipeline import run_feature_pipeline
    t0 = time.time()
    merged_path = run_feature_pipeline(
        as_of_timestamp=args.as_of,
        output_dir=config.FEATURES_DIR,
        skip_existing=not args.force,
    )
    log.info(f"Feature build complete in {time.time()-t0:.1f}s → {merged_path}")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND: features audit
# ─────────────────────────────────────────────────────────────────────────────
def cmd_features_audit(args):
    from civix_ml.evaluation.leakage import assert_no_leakage, check_future_timestamps
    import duckdb

    merged = config.FEATURES_DIR / "features_merged.parquet"
    if not merged.exists():
        log.error(f"Feature matrix not found: {merged}. Run `features build` first.")
        sys.exit(1)

    con = duckdb.connect(":memory:")
    df  = con.execute(f"SELECT * FROM read_parquet('{str(merged).replace(chr(92),'/')}')").df()
    con.close()

    log.info(f"Feature matrix: {df.shape[0]:,} persons × {df.shape[1]} columns")

    # Gate 1: Leakage
    assert_no_leakage(df, label="merged feature matrix")

    # Gate 2: Temporal
    ts_cols = [c for c in df.columns if "_ts" in c.lower()]
    check_future_timestamps(df, args.as_of, ts_cols)

    # Statistics
    numeric = df.select_dtypes(include=[np.number])
    stats = numeric.describe(percentiles=[.05, .25, .5, .75, .95]).T
    stats["missing_rate"] = df[numeric.columns].isnull().mean()
    stats_path = config.REPORTS_DIR / "FEATURE_STATISTICS.md"

    with open(stats_path, "w", encoding="utf-8") as f:
        f.write("# CIVIX Phase 3A — Feature Statistics\n\n")
        f.write(f"Shape: {df.shape[0]:,} rows × {df.shape[1]} columns\n\n")
        f.write(stats.round(4).to_markdown())
    log.info(f"Feature statistics written to {stats_path}")

    # Catalog
    catalog_path = config.REPORTS_DIR / "FEATURE_CATALOG.md"
    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write("# CIVIX Phase 3A — Feature Catalog\n\n")
        f.write("| Feature | Type | Missing Rate | Min | Max | Mean |\n")
        f.write("|---------|------|-------------|-----|-----|------|\n")
        for col in df.columns:
            col_data = df[col]
            dtype = str(col_data.dtype)
            miss  = col_data.isnull().mean()
            if col_data.dtype in [np.float64, np.int64, np.float32]:
                mn = col_data.min(); mx = col_data.max(); mu = col_data.mean()
                f.write(f"| `{col}` | {dtype} | {miss:.3f} | {mn:.2f} | {mx:.2f} | {mu:.2f} |\n")
            else:
                f.write(f"| `{col}` | {dtype} | {miss:.3f} | — | — | — |\n")

    log.info(f"Feature catalog written to {catalog_path}")
    log.info("Feature audit PASSED.")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND: train (Phase 3A)
# ─────────────────────────────────────────────────────────────────────────────
def cmd_train(args):
    from civix_ml.features.feature_pipeline import load_training_data
    from civix_ml.models.baselines import (
        train_logistic_regression, train_random_forest,
        train_xgboost, train_isolation_forest, _save_model,
    )
    from civix_ml.evaluation.metrics import evaluate, evaluate_isolation_forest
    from civix_ml.evaluation.leakage import assert_no_leakage

    set_global_seed(args.seed)
    merged = config.FEATURES_DIR / "features_merged.parquet"
    if not merged.exists():
        log.error("Run `features build` first."); sys.exit(1)

    log.info(f"Loading TRAIN split ...")
    X_train, y_train, y_sc_train = load_training_data(merged, split="TRAIN")
    log.info(f"Loading VALIDATION split ...")
    X_val,   y_val,   y_sc_val   = load_training_data(merged, split="VALIDATION")

    # Final leakage gate before training
    assert_no_leakage(X_train, "X_train")

    model_name = args.model.lower().replace("-", "_").replace(" ", "_")
    t0 = time.time()

    if model_name in ("logistic", "logistic_regression", "lr"):
        model, elapsed = train_logistic_regression(X_train, y_train, seed=args.seed)
        scores_val = model.predict_proba(X_val)[:, 1]
        metrics = evaluate(np.array(y_val), scores_val, model_name="LogisticRegression")
        _save_model(model, "logistic_regression", metrics, list(X_train.columns), args.seed)

    elif model_name in ("rf", "random_forest"):
        model, elapsed = train_random_forest(X_train, y_train, seed=args.seed)
        scores_val = model.predict_proba(X_val)[:, 1]
        metrics = evaluate(np.array(y_val), scores_val, model_name="RandomForest")
        # Feature importance
        fi = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
        fi_path = config.REPORTS_DIR / "RF_FEATURE_IMPORTANCE.md"
        with open(fi_path, "w", encoding="utf-8") as f:
            f.write("# Random Forest Feature Importance\n\n")
            f.write(fi.head(30).to_markdown())
        log.info(f"Feature importance saved to {fi_path}")
        _save_model(model, "random_forest", metrics, list(X_train.columns), args.seed)

    elif model_name in ("xgb", "xgboost"):
        model, elapsed = train_xgboost(X_train, y_train, X_val, y_val, seed=args.seed)
        scores_val = model.predict_proba(X_val)[:, 1]
        metrics = evaluate(np.array(y_val), scores_val, model_name="XGBoost")
        # Feature importance
        fi = pd.Series(model.feature_importances_, index=X_train.columns).sort_values(ascending=False)
        fi_path = config.REPORTS_DIR / "XGB_FEATURE_IMPORTANCE.md"
        with open(fi_path, "w", encoding="utf-8") as f:
            f.write("# XGBoost Feature Importance\n\n")
            f.write(fi.head(30).to_markdown())
        _save_model(model, "xgboost", metrics, list(X_train.columns), args.seed)

    elif model_name in ("if", "isolation_forest"):
        model, elapsed = train_isolation_forest(X_train, seed=args.seed)
        raw_scores = model.score_samples(X_val)
        metrics = evaluate_isolation_forest(np.array(y_val), raw_scores, model_name="IsolationForest")
        _save_model(model, "isolation_forest", metrics, list(X_train.columns), args.seed)

    else:
        log.error(f"Unknown model: {args.model}. Choose: logistic, random_forest, xgboost, isolation_forest")
        sys.exit(1)

    # Save experiment record
    exp = {
        "model": model_name,
        "seed": args.seed,
        "as_of": args.as_of,
        "feature_version": config.FEATURE_VERSION,
        "train_samples": len(X_train),
        "val_samples":   len(X_val),
        "n_features":    X_train.shape[1],
        "train_time_sec": round(time.time()-t0, 1),
        "val_metrics": metrics,
    }
    exp_path = config.EXPERIMENTS_DIR / f"{model_name}_{time.strftime('%Y%m%dT%H%M%S')}.json"
    exp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(exp_path, "w") as f:
        json.dump(exp, f, indent=2)
    log.info(f"Experiment record saved to {exp_path}")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND: evaluate (Phase 3A)
# ─────────────────────────────────────────────────────────────────────────────
def cmd_evaluate(args):
    from civix_ml.features.feature_pipeline import load_training_data
    from civix_ml.evaluation.metrics import evaluate, evaluate_isolation_forest

    merged = config.FEATURES_DIR / "features_merged.parquet"
    if not merged.exists():
        log.error("Run `features build` first."); sys.exit(1)

    log.info("Loading TEST split (final evaluation) ...")
    X_test, y_test, y_sc_test = load_training_data(merged, split="TEST")

    # Load all saved models and evaluate on TEST
    registry = config.MODELS_DIR / "registry"
    all_metrics = []
    for model_dir in sorted(registry.iterdir()):
        pkl = model_dir / "model.pkl"
        meta_f = model_dir / "metadata.json"
        if not pkl.exists(): continue
        with open(pkl, "rb") as f: model = pickle.load(f)
        with open(meta_f) as f: meta = json.load(f)
        name = meta["model_name"]
        log.info(f"Evaluating {name} on TEST set ...")
        if hasattr(model, "predict_proba"):
            scores = model.predict_proba(X_test)[:, 1]
            m = evaluate(np.array(y_test), scores, model_name=name)
        elif hasattr(model, "score_samples"):
            scores = -model.score_samples(X_test)
            m = evaluate_isolation_forest(np.array(y_test), -scores, model_name=name)
        else:
            continue
        all_metrics.append(m)

    # Write comparison table
    if all_metrics:
        df_m = pd.DataFrame(all_metrics)
        report_path = config.REPORTS_DIR / "BASELINE_MODEL_REPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("# CIVIX Phase 3A — Baseline Model Report (TEST SET)\n\n")
            f.write("> All metrics computed on the held-out TEST split (37,500 persons).\n\n")
            cols = ["model","pr_auc","roc_auc","precision","recall","f1",
                    "precision_at_1pct","recall_at_1pct","precision_at_5pct",
                    "recall_at_5pct","false_positive_rate","brier_score"]
            f.write(df_m[cols].to_markdown(index=False))
        log.info(f"Baseline model report saved to {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# COMMAND: adversarial (Phase 3A)
# ─────────────────────────────────────────────────────────────────────────────
def cmd_adversarial(args):
    import duckdb
    from civix_ml.features.feature_pipeline import load_training_data
    from civix_ml.evaluation.adversarial import run_adversarial_tests

    merged = config.FEATURES_DIR / "features_merged.parquet"
    X_test, y_test, y_sc_test = load_training_data(merged, split="TEST")

    # Load y_fp
    con = duckdb.connect(":memory:")
    labs  = config.LABELS_GLOB.replace("\\", "/")
    splits = config.SPLITS_GLOB.replace("\\", "/")
    feat   = str(merged).replace("\\", "/")
    fp_df = con.execute(f"""
        SELECT f.person_id, l.is_false_positive
        FROM read_parquet('{feat}') f
        JOIN read_parquet('{splits}') s ON s.entity_id = f.person_id
        JOIN read_parquet('{labs}') l ON l.entity_id = f.person_id
        WHERE s.split = 'TEST'
    """).df()
    con.close()
    y_fp = fp_df["is_false_positive"]

    registry = config.MODELS_DIR / "registry"
    adv_results = {}
    for model_dir in sorted(registry.iterdir()):
        pkl = model_dir / "model.pkl"
        meta_f = model_dir / "metadata.json"
        if not pkl.exists(): continue
        with open(pkl, "rb") as f: model = pickle.load(f)
        with open(meta_f) as f: meta = json.load(f)
        name = meta["model_name"]
        log.info(f"Adversarial tests for {name} ...")
        r = run_adversarial_tests(X_test, y_test, y_sc_test, y_fp, model, name, list(X_test.columns))
        adv_results[name] = r

    report_path = config.REPORTS_DIR / "ADVERSARIAL_EVALUATION_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# CIVIX Phase 3A — Adversarial Evaluation Report\n\n")
        for m_name, res in adv_results.items():
            f.write(f"## {m_name}\n\n")
            for k, v in res.items():
                if isinstance(v, dict):
                    f.write(f"### {k}\n```json\n{json.dumps(v, indent=2)}\n```\n\n")
                else:
                    f.write(f"- **{k}**: {v}\n")
            f.write("\n")
    log.info(f"Adversarial report saved to {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph build
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_build(args):
    from civix_ml.graph.mappings import build_mappings
    from civix_ml.graph.node_builder import build_all_nodes
    from civix_ml.graph.cdr_graph import build_cdr_aggregated_edges, build_cdr_temporal_edges
    from civix_ml.graph.transaction_graph import build_txn_aggregated_edges

    log.info("=== Phase 3B: Graph Build ===")
    t0 = time.time()
    build_mappings(force=args.force)
    build_all_nodes(force=args.force)
    if not args.skip_temporal:
        build_cdr_temporal_edges(as_of_timestamp=args.as_of, force=args.force)
    build_cdr_aggregated_edges(as_of_timestamp=args.as_of, force=args.force)
    build_txn_aggregated_edges(as_of_timestamp=args.as_of, force=args.force)
    log.info(f"Graph build complete in {time.time()-t0:.1f}s")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph stats
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_stats(args):
    from civix_ml.graph.graph_statistics import compute_graph_statistics
    stats = compute_graph_statistics()
    log.info("Graph statistics:")
    for k, v in stats.items():
        log.info(f"  {k}: {json.dumps(v)}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph features
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_features(args):
    from civix_ml.graph.features import build_graph_features
    from civix_ml.evaluation.graph_leakage import check_graph_features

    t0 = time.time()
    df = build_graph_features(as_of_timestamp=args.as_of, force=args.force)
    check_graph_features(df.drop(columns=["person_id"], errors="ignore"),
                         name="graph_features")
    log.info(f"Graph features built in {time.time()-t0:.1f}s: {df.shape}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph validate
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_validate(args):
    from civix_ml.graph.temporal_split import validate_temporal_graph
    from civix_ml.graph.schema import GRAPH_EDGES_DIR

    cdr_agg = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet")
    txn_agg = str(GRAPH_EDGES_DIR / "txn_aggregated" / "txn_aggregated.parquet")

    results = []
    for path, ts_col in [(cdr_agg, "first_contact"), (txn_agg, "first_txn")]:
        r = validate_temporal_graph(path, ts_col, args.as_of)
        results.append(r)
        if not r["passed"]:
            log.error(f"TEMPORAL LEAKAGE in {path}!")
            sys.exit(1)
    log.info("All temporal graph validation gates PASSED.")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph baseline
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_baseline(args):
    from civix_ml.models.graph_baselines import train_graph_model
    model_name = args.model or "xgboost"
    rec = train_graph_model(model_name, feature_set="graph")
    log.info(f"Graph baseline [{model_name}] TEST PR-AUC: {rec['test_metrics'].get('pr_auc', '?')}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph compare (three-way comparison)
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_compare(args):
    from civix_ml.models.graph_baselines import run_three_way_comparison
    phase3b_dir = config.ROOT_DIR / "docs" / "phase3b"
    phase3b_dir.mkdir(parents=True, exist_ok=True)

    log.info("Running three-way comparison: behavioral vs graph vs combined ...")
    df = run_three_way_comparison()

    report_path = phase3b_dir / "PHASE3B_MODEL_COMPARISON.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# CIVIX Phase 3B — Three-Way Model Comparison\n\n")
        f.write("> Comparison of behavioral-only, graph-only, and combined feature sets.\n\n")
        f.write("> PR-AUC is the primary metric. Isolation Forest is the only unsupervised model.\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n## Interpretation\n")
        f.write("- If graph-only PR-AUC > behavioral-only: graph topology provides independent signal.\n")
        f.write("- If combined > both: graph and behavioral are complementary.\n")
        f.write("- If supervised models achieve 1.0: synthetic separability artifact — "
                "check artifact audit before celebrating.\n")
    log.info(f"Comparison report saved to {report_path}")
    print(df.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: graph audit (synthetic artifact scan)
# ─────────────────────────────────────────────────────────────────────────────
def cmd_graph_audit(args):
    from civix_ml.graph.graph_statistics import compute_degree_by_scenario
    phase3b_dir = config.ROOT_DIR / "docs" / "phase3b"
    phase3b_dir.mkdir(parents=True, exist_ok=True)

    log.info("Running graph synthetic artifact audit ...")
    df = compute_degree_by_scenario()
    log.info(f"\nDegree by scenario:\n{df.to_string(index=False)}")

    # Check for artifacts: near-zero std within scenario
    artifact_signals = []
    for _, row in df.iterrows():
        cv = row["std_out_degree"] / (abs(row["mean_out_degree"]) + 1e-9)
        if cv < 0.05:
            artifact_signals.append(f"  ARTIFACT: {row['scenario_class']} — degree CV={cv:.4f} (near-zero variance)")

    report_path = phase3b_dir / "GRAPH_SYNTHETIC_ARTIFACT_REPORT.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# CIVIX Phase 3B — Graph Synthetic Artifact Report\n\n")
        f.write("## Degree Distribution by Scenario Class\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n## Artifact Assessment\n\n")
        if artifact_signals:
            f.write("⚠️ **ARTIFACTS DETECTED:**\n")
            for sig in artifact_signals:
                f.write(f"- {sig}\n")
        else:
            f.write("✅ No near-zero within-class variance found in degree features.\n")
            f.write("Graph features do not show the same hardcoded-constant pattern as Phase 3A behavioral features.\n")
    log.info(f"Graph artifact report saved to {report_path}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3B: gnn train
# ─────────────────────────────────────────────────────────────────────────────
def cmd_gnn_train(args):
    try:
        import torch
    except ImportError:
        log.error("PyTorch not installed. Run: pip install torch --index-url https://download.pytorch.org/whl/cu128")
        sys.exit(1)
    try:
        from torch_geometric.nn import SAGEConv
    except ImportError:
        log.error("PyTorch Geometric not installed. Run: pip install torch_geometric")
        sys.exit(1)

    from civix_ml.models.gnn import GraphSAGEConfig, build_pyg_data, train_graphsage
    from civix_ml.models.graph_baselines import load_graph_features, load_combined_features
    from civix_ml.graph.schema import GRAPH_EDGES_DIR, GRAPH_MAPPINGS_DIR

    log.info("=== GNN Training: GraphSAGE ===")
    cfg = GraphSAGEConfig(
        hidden_channels=args.hidden_dim,
        num_layers=args.layers,
        dropout=args.dropout,
        lr=args.lr,
        epochs=args.epochs,
        batch_size=args.batch_size,
        fanout=[int(x) for x in args.fanout.split(",")],
        device=args.device,
        seed=args.seed,
    )

    # Load graph features (node attributes)
    log.info("Loading graph features for GNN node attributes ...")
    X_train, y_train, _ = load_graph_features("TRAIN")
    X_val,   y_val,   _ = load_graph_features("VALIDATION")
    X_test,  y_test,  _ = load_graph_features("TEST")

    # Load phone mapping and CDR edges with integer indices
    import pyarrow.parquet as pq
    import pandas as pd
    phone_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "phone_mapping.parquet")).to_pandas()
    person_map_df = pq.read_table(str(GRAPH_MAPPINGS_DIR / "person_mapping.parquet")).to_pandas()

    cdr_agg_path = str(GRAPH_EDGES_DIR / "cdr_aggregated" / "cdr_aggregated.parquet")
    edges_raw = pq.read_table(cdr_agg_path).to_pandas()[["src", "dst"]]

    phone_to_idx = dict(zip(phone_map_df["entity_id"], phone_map_df["node_idx"]))
    edges_raw["src_node_idx"] = edges_raw["src"].map(phone_to_idx)
    edges_raw["dst_node_idx"] = edges_raw["dst"].map(phone_to_idx)
    edges_raw = edges_raw.dropna(subset=["src_node_idx", "dst_node_idx"])
    edges_raw = edges_raw.astype({"src_node_idx": int, "dst_node_idx": int})

    # Build person-level node feature matrix
    person_to_idx = dict(zip(person_map_df["entity_id"], person_map_df["node_idx"]))
    all_persons_df = pd.concat([
        X_train.assign(split="TRAIN"),
        X_val.assign(split="VALIDATION"),
        X_test.assign(split="TEST"),
    ], ignore_index=True)
    # Need person_ids — reload with person_id
    from civix_ml.utils.duckdb_utils import get_connection
    from civix_ml.graph.schema import GRAPH_FEATURES_DIR
    con = get_connection()
    feat_path = str(GRAPH_FEATURES_DIR / "graph_features.parquet").replace("\\", "/")
    labs_path = config.LABELS_GLOB.replace("\\", "/")
    splits_path = config.SPLITS_GLOB.replace("\\", "/")
    full_df = con.execute(f"""
        SELECT g.person_id, g.* EXCLUDE(person_id),
               l.is_positive_label, s.split
        FROM read_parquet('{feat_path}') g
        JOIN read_parquet('{splits_path}') s ON s.entity_id = g.person_id
        JOIN read_parquet('{labs_path}') l ON l.entity_id = g.person_id
    """).df()
    con.close()

    full_df["node_idx"] = full_df["person_id"].map(person_to_idx)
    full_df = full_df.dropna(subset=["node_idx"]).sort_values("node_idx")
    feat_cols = [c for c in X_train.columns]
    node_feats = full_df[feat_cols].fillna(0)
    node_feats_df = full_df[["node_idx"] + feat_cols].fillna(0)

    log.info(f"  Node features: {node_feats.shape}")
    log.info(f"  Edge list: {len(edges_raw):,} phone-level edges")
    log.info("  NOTE: Phone→Phone edges are used as proxy for Person→Person edges.")

    # Build masks
    import torch
    train_mask = torch.tensor(full_df["split"].values == "TRAIN", dtype=torch.bool)
    val_mask   = torch.tensor(full_df["split"].values == "VALIDATION", dtype=torch.bool)
    test_mask  = torch.tensor(full_df["split"].values == "TEST", dtype=torch.bool)
    labels     = torch.tensor(full_df["is_positive_label"].astype(int).values, dtype=torch.long)

    from torch_geometric.data import Data
    x = torch.tensor(node_feats.values, dtype=torch.float32)

    # Build person-level edges by mapping phone edges to person edges via phone->person
    from civix_ml.utils.duckdb_utils import get_connection as gc
    con2 = gc()
    cdrs_g = config.CDR_GLOB.replace("\\", "/")
    phone_person = con2.execute(f"""
        SELECT DISTINCT caller_phone_id AS phone_id, caller_person_id AS person_id 
        FROM read_parquet('{cdrs_g}')
        WHERE caller_person_id IS NOT NULL
    """).df()
    con2.close()
    pp_map = dict(zip(phone_person["phone_id"], phone_person["person_id"]))

    edges_raw["src_person_id"] = edges_raw["src"].map(pp_map)
    edges_raw["dst_person_id"] = edges_raw["dst"].map(pp_map)
    person_edges = edges_raw.dropna(subset=["src_person_id", "dst_person_id"])
    person_edges["src_pidx"] = person_edges["src_person_id"].map(person_to_idx)
    person_edges["dst_pidx"] = person_edges["dst_person_id"].map(person_to_idx)
    person_edges = person_edges.dropna(subset=["src_pidx", "dst_pidx"])
    person_edges = person_edges.drop_duplicates(subset=["src_pidx", "dst_pidx"])
    person_edges = person_edges.astype({"src_pidx": int, "dst_pidx": int})

    edge_index = torch.tensor(
        person_edges[["src_pidx", "dst_pidx"]].values.T, dtype=torch.long
    )
    log.info(f"  Person-level edges: {edge_index.shape[1]:,}")

    data = Data(x=x, edge_index=edge_index, y=labels)

    model_dir = config.MODELS_DIR / "registry" / f"graphsage_{time.strftime('%Y%m%dT%H%M%S')}"
    result = train_graphsage(data, train_mask, val_mask, cfg, model_dir)
    log.info(f"GNN training complete. Best val_loss={result['best_val_loss']:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# ARGUMENT PARSER
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(prog="civix_ml", description="CIVIX ML Pipeline")
    parser.add_argument("--seed",   type=int,   default=config.GLOBAL_SEED)
    parser.add_argument("--as-of",  type=str,   default=config.DEFAULT_AS_OF, dest="as_of")
    parser.add_argument("--force",  action="store_true", help="Re-build even if cached")

    sub = parser.add_subparsers(dest="command")

    # ── Phase 3A ──────────────────────────────────────────────────────────────
    feat_p = sub.add_parser("features", help="Phase 3A feature commands")
    feat_sub = feat_p.add_subparsers(dest="feat_command")
    feat_sub.add_parser("build")
    feat_sub.add_parser("audit")

    train_p = sub.add_parser("train", help="Train a Phase 3A baseline model")
    train_p.add_argument("--model", type=str, required=True,
                         choices=["logistic","random_forest","xgboost","isolation_forest"])

    sub.add_parser("evaluate",   help="Evaluate Phase 3A models on TEST set")
    sub.add_parser("adversarial",help="Phase 3A adversarial tests")

    # ── Phase 3B graph commands ───────────────────────────────────────────────
    graph_p = sub.add_parser("graph", help="Phase 3B graph commands")
    graph_sub = graph_p.add_subparsers(dest="graph_command")

    graph_build_p = graph_sub.add_parser("build",    help="Build CDR + txn graph edge lists")
    graph_build_p.add_argument("--skip-temporal", action="store_true", dest="skip_temporal",
                               help="Skip building raw temporal CDR edges (slow, 75M rows)")
                               
    graph_sub.add_parser("stats",    help="Compute graph statistics")
    graph_sub.add_parser("features", help="Build person-level graph structural features")
    graph_sub.add_parser("validate", help="Temporal and leakage validation")

    gb_p = graph_sub.add_parser("baseline", help="Train graph-only baseline models")
    gb_p.add_argument("--model", type=str, default="xgboost",
                      choices=["logistic","random_forest","xgboost","isolation_forest"])

    graph_sub.add_parser("compare",  help="Three-way behavioral vs graph vs combined comparison")
    graph_sub.add_parser("audit",    help="Graph synthetic artifact audit")

    # ── Phase 3B GNN commands ─────────────────────────────────────────────────
    gnn_p = sub.add_parser("gnn", help="Phase 3B GNN commands")
    gnn_sub = gnn_p.add_subparsers(dest="gnn_command")

    gnn_train_p = gnn_sub.add_parser("train", help="Train GraphSAGE GNN")
    gnn_train_p.add_argument("--hidden-dim",  type=int,   default=64,   dest="hidden_dim")
    gnn_train_p.add_argument("--layers",      type=int,   default=2)
    gnn_train_p.add_argument("--dropout",     type=float, default=0.3)
    gnn_train_p.add_argument("--lr",          type=float, default=1e-3)
    gnn_train_p.add_argument("--epochs",      type=int,   default=50)
    gnn_train_p.add_argument("--batch-size",  type=int,   default=512,  dest="batch_size")
    gnn_train_p.add_argument("--fanout",      type=str,   default="15,10")
    gnn_train_p.add_argument("--device",      type=str,   default="auto",
                              choices=["auto","cpu","cuda"])
    gnn_sub.add_parser("evaluate", help="Evaluate trained GNN on TEST set")

    args = parser.parse_args()

    # Attach defaults for graph commands that need them
    if not hasattr(args, "skip_temporal"):
        args.skip_temporal = False

    if args.command == "features":
        if args.feat_command == "build":
            cmd_features_build(args)
        elif args.feat_command == "audit":
            cmd_features_audit(args)
        else:
            feat_p.print_help()
    elif args.command == "train":
        cmd_train(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "adversarial":
        cmd_adversarial(args)
    elif args.command == "graph":
        if args.graph_command == "build":
            cmd_graph_build(args)
        elif args.graph_command == "stats":
            cmd_graph_stats(args)
        elif args.graph_command == "features":
            cmd_graph_features(args)
        elif args.graph_command == "validate":
            cmd_graph_validate(args)
        elif args.graph_command == "baseline":
            cmd_graph_baseline(args)
        elif args.graph_command == "compare":
            cmd_graph_compare(args)
        elif args.graph_command == "audit":
            cmd_graph_audit(args)
        else:
            graph_p.print_help()
    elif args.command == "gnn":
        if args.gnn_command == "train":
            cmd_gnn_train(args)
        else:
            gnn_p.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()


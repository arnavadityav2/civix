"""
CIVIX Graph ML Baselines — Phase 3B
Trains graph-only, behavioral-only, and combined models.
Runs the three-way comparison to answer: does graph topology add signal?
"""
import json
import time
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb

from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.evaluation.metrics import evaluate, evaluate_isolation_forest
from civix_ml.evaluation.graph_leakage import check_graph_features
from civix_ml.features.feature_pipeline import load_training_data
from civix_ml.graph.schema import GRAPH_FEATURES_DIR
from civix_ml.models.baselines import (
    train_logistic_regression,
    train_random_forest,
    train_xgboost,
    train_isolation_forest,
    _save_model
)

log = get_logger(__name__)


def load_graph_features(split: str = "TRAIN") -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """
    Load graph features + labels for a split.
    Uses same splits as Phase 3A (entity_id = person_id).
    """
    from civix_ml.utils.duckdb_utils import get_connection
    con = get_connection()

    graph_feat = str(GRAPH_FEATURES_DIR / "graph_features.parquet").replace("\\", "/")
    labs   = config.LABELS_GLOB.replace("\\", "/")
    splits = config.SPLITS_GLOB.replace("\\", "/")

    sql = f"""
    SELECT
        g.*,
        l.scenario_class,
        l.is_positive_label,
        l.is_false_positive,
        l.difficulty
    FROM read_parquet('{graph_feat}') g
    JOIN read_parquet('{splits}') s ON s.entity_id = g.person_id
    JOIN read_parquet('{labs}')   l ON l.entity_id = g.person_id
    WHERE s.split = '{split}'
    """
    df = con.execute(sql).df()
    con.close()

    label_cols = ["scenario_class", "is_positive_label", "is_false_positive", "difficulty"]
    y_binary   = df["is_positive_label"].astype(int)
    y_scenario = df["scenario_class"]

    drop_cols  = ["person_id"] + label_cols
    X = df.drop(columns=drop_cols, errors="ignore")

    # Leakage check
    check_graph_features(X, name=f"graph_features_{split}")

    # Fill NaN
    X = X.fillna(0)
    log.info(f"  Graph features [{split}]: {len(X):,} persons × {X.shape[1]} features")
    return X, y_binary, y_scenario


def load_combined_features(split: str = "TRAIN") -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Load behavioral + graph features merged on person_id."""
    from civix_ml.utils.duckdb_utils import get_connection
    con = get_connection()

    beh_feat   = str(config.FEATURES_DIR / "features_merged.parquet").replace("\\", "/")
    graph_feat = str(GRAPH_FEATURES_DIR / "graph_features.parquet").replace("\\", "/")
    labs   = config.LABELS_GLOB.replace("\\", "/")
    splits = config.SPLITS_GLOB.replace("\\", "/")

    artifacts = ", ".join([f"b.{c}" for c in config.GENERATOR_ARTIFACT_FEATURES
                           if c not in ["first_call_ts","last_call_ts","first_txn_ts","last_txn_ts"]])

    sql = f"""
    SELECT
        b.person_id,
        b.* EXCLUDE(person_id, first_call_ts, last_call_ts, first_txn_ts, last_txn_ts,
                    avg_duration_sec, std_duration_sec, max_duration_sec, min_duration_sec,
                    long_call_ratio, total_txns, active_txn_days, txns_per_active_day,
                    night_txn_ratio, has_both_activity, night_activity_product),
        g.* EXCLUDE(person_id),
        l.scenario_class,
        l.is_positive_label,
        l.is_false_positive,
        l.difficulty
    FROM read_parquet('{beh_feat}') b
    JOIN read_parquet('{graph_feat}') g ON g.person_id = b.person_id
    JOIN read_parquet('{splits}') s ON s.entity_id = b.person_id
    JOIN read_parquet('{labs}')   l ON l.entity_id = b.person_id
    WHERE s.split = '{split}'
    """
    df = con.execute(sql).df()
    con.close()

    label_cols = ["scenario_class", "is_positive_label", "is_false_positive", "difficulty"]
    y_binary   = df["is_positive_label"].astype(int)
    y_scenario = df["scenario_class"]
    X = df.drop(columns=["person_id"] + label_cols, errors="ignore")

    # One-hot encode low-cardinality strings
    cat_cols = X.select_dtypes(include=["object"]).columns.tolist()
    safe_cat = [c for c in cat_cols if X[c].nunique() < 50]
    high_card = [c for c in cat_cols if c not in safe_cat]
    if high_card:
        X = X.drop(columns=high_card)
    if safe_cat:
        X = pd.get_dummies(X, columns=safe_cat, drop_first=True, dtype=float)

    X = X.fillna(0)
    log.info(f"  Combined features [{split}]: {len(X):,} persons × {X.shape[1]} features")
    return X, y_binary, y_scenario


def _build_model(model_name: str, n_pos: int, n_neg: int):
    """Return unfitted sklearn/xgboost model."""
    ratio = n_neg / max(n_pos, 1)
    if model_name == "logistic":
        return Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, class_weight="balanced",
                                        random_state=config.GLOBAL_SEED, C=1.0)),
        ])
    elif model_name == "random_forest":
        return RandomForestClassifier(
            n_estimators=200, class_weight="balanced",
            random_state=config.GLOBAL_SEED, n_jobs=-1, max_depth=12
        )
    elif model_name == "xgboost":
        return xgb.XGBClassifier(
            n_estimators=300, learning_rate=0.05, max_depth=6,
            scale_pos_weight=ratio, use_label_encoder=False,
            eval_metric="logloss", random_state=config.GLOBAL_SEED,
            n_jobs=4, verbosity=0,
        )
    elif model_name == "isolation_forest":
        return IsolationForest(
            n_estimators=200, contamination=0.10,
            random_state=config.GLOBAL_SEED, n_jobs=-1
        )
    else:
        raise ValueError(f"Unknown model: {model_name}")


def train_graph_model(model_name: str, feature_set: str = "graph") -> dict:
    """
    Train one model on the specified feature set.
    feature_set: "graph" | "behavioral" | "combined"
    """
    log.info(f"\n{'='*60}")
    log.info(f"Training {model_name} on [{feature_set}] features ...")

    # Load data
    if feature_set == "graph":
        X_train, y_train, _ = load_graph_features("TRAIN")
        X_val,   y_val,   _ = load_graph_features("VALIDATION")
        X_test,  y_test,  _ = load_graph_features("TEST")
    elif feature_set == "behavioral":
        feat_path = config.FEATURES_DIR / "features_merged.parquet"
        X_train, y_train, _ = load_training_data(feat_path, "TRAIN")
        X_val,   y_val,   _ = load_training_data(feat_path, "VALIDATION")
        X_test,  y_test,  _ = load_training_data(feat_path, "TEST")
    elif feature_set == "combined":
        X_train, y_train, _ = load_combined_features("TRAIN")
        X_val,   y_val,   _ = load_combined_features("VALIDATION")
        X_test,  y_test,  _ = load_combined_features("TEST")
    else:
        raise ValueError(f"Unknown feature_set: {feature_set}")

    n_pos = int(y_train.sum())
    n_neg = int((y_train == 0).sum())
    log.info(f"  pos={n_pos:,}, neg={n_neg:,}, ratio={n_neg/max(n_pos,1):.1f}")

    model = _build_model(model_name, n_pos, n_neg)

    t0 = time.time()
    if model_name == "isolation_forest":
        model.fit(X_train)
        scores_val  = -model.score_samples(X_val)
        scores_test = -model.score_samples(X_test)
        # Convert to pseudo-probabilities [0,1]
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        scores_val  = scaler.fit_transform(scores_val.reshape(-1,1)).flatten()
        scores_test = scaler.transform(scores_test.reshape(-1,1)).flatten()
        y_pred_val  = (scores_val > 0.5).astype(int)
        y_pred_test = (scores_test > 0.5).astype(int)
        val_metrics  = evaluate(y_val,  scores_val,  model_name=f"{model_name}_{feature_set}_val", threshold=0.5)
        test_metrics = evaluate(y_test, scores_test, model_name=f"{model_name}_{feature_set}_test", threshold=0.5)
    else:
        model.fit(X_train, y_train)
        scores_val  = model.predict_proba(X_val)[:, 1]
        scores_test = model.predict_proba(X_test)[:, 1]
        val_metrics   = evaluate(y_val,  scores_val,  model_name=f"{model_name}_{feature_set}_val", threshold=0.5)
        test_metrics  = evaluate(y_test, scores_test, model_name=f"{model_name}_{feature_set}_test", threshold=0.5)

    elapsed = time.time() - t0
    log.info(f"  Trained in {elapsed:.1f}s")

    # Save model
    import joblib
    ts = time.strftime("%Y%m%dT%H%M%S")
    model_id = f"{feature_set}_{model_name}_{ts}"
    REGISTRY_DIR = config.MODELS_DIR / "registry"
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    model_dir = REGISTRY_DIR / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "model.pkl")
    record = {
        "model_id":    model_id,
        "model_name":  model_name,
        "feature_set": feature_set,
        "n_features":  X_train.shape[1],
        "train_size":  len(X_train),
        "val_metrics": val_metrics,
        "test_metrics": test_metrics,
        "train_seconds": elapsed,
        "features":    list(X_train.columns),
        "seed":        config.GLOBAL_SEED,
    }
    (config.EXPERIMENTS_DIR / f"{model_id}.json").write_text(
        json.dumps(record, indent=2, default=str)
    )
    log.info(f"  Saved → {model_dir}")
    return record


def run_three_way_comparison(model_names: list[str] = None) -> pd.DataFrame:
    """
    Train all models on behavioral, graph, and combined feature sets.
    Returns a comparison DataFrame.
    """
    if model_names is None:
        model_names = ["logistic", "random_forest", "xgboost", "isolation_forest"]

    feature_sets = ["behavioral", "graph", "combined"]
    results = []

    for fs in feature_sets:
        for mn in model_names:
            try:
                rec = train_graph_model(mn, fs)
                row = {
                    "feature_set": fs,
                    "model":       mn,
                    "pr_auc":      rec["test_metrics"].get("pr_auc", 0),
                    "roc_auc":     rec["test_metrics"].get("roc_auc", 0),
                    "p_at_1pct":   rec["test_metrics"].get("precision_at_1pct", 0),
                    "r_at_1pct":   rec["test_metrics"].get("recall_at_1pct", 0),
                    "f1":          rec["test_metrics"].get("f1", 0),
                    "fp_rate":     rec["test_metrics"].get("false_positive_rate", 0),
                    "n_features":  rec["n_features"],
                }
                results.append(row)
            except Exception as e:
                log.error(f"  FAILED [{fs}/{mn}]: {e}")
                results.append({"feature_set": fs, "model": mn, "error": str(e)})

    return pd.DataFrame(results)

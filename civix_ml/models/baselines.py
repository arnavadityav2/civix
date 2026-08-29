"""Baseline ML models for CIVIX Phase 3A."""
import json
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import pickle

from civix_ml import config
from civix_ml.utils import get_logger
from civix_ml.utils.reproducibility import set_global_seed

log = get_logger(__name__)

try:
    raise ImportError("Bypassing XGBoost import to avoid CUDA hang")
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    log.warning("XGBoost not installed. Skipping XGBoost model.")


def _save_model(model, name: str, metrics: dict, feature_names: list, seed: int):
    """Save model artifact + metadata to registry."""
    ts = time.strftime("%Y%m%dT%H%M%S")
    model_dir = config.MODELS_DIR / "registry" / f"{name}_{ts}"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Save model
    with open(model_dir / "model.pkl", "wb") as f:
        pickle.dump(model, f)

    # Save metadata
    meta = {
        "model_name": name,
        "training_timestamp": ts,
        "dataset_profile": "profile_c",
        "feature_version": config.FEATURE_VERSION,
        "random_seed": seed,
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "metrics": metrics,
        "label_definition": "is_positive_label (confirmed_pattern=1)",
        "dataset_manifest": str(config.PROFILE_C_DIR / "manifest.json"),
    }
    with open(model_dir / "metadata.json", "w") as f:
        json.dump(meta, f, indent=2)

    log.info(f"  Model saved to {model_dir}")
    return model_dir


def train_logistic_regression(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    seed: int = config.GLOBAL_SEED,
) -> tuple:
    set_global_seed(seed)
    log.info("Training Logistic Regression ...")
    t0 = time.time()

    # Class weights to handle imbalance
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            class_weight="balanced",
            max_iter=500,
            random_state=seed,
            solver="lbfgs",
            C=1.0,
        ))
    ])
    model.fit(X_train, y_train)
    elapsed = time.time() - t0
    log.info(f"  Trained in {elapsed:.1f}s")
    return model, elapsed


def train_random_forest(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    seed: int = config.GLOBAL_SEED,
) -> tuple:
    set_global_seed(seed)
    log.info("Training Random Forest ...")
    t0 = time.time()

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
        min_samples_leaf=5,
    )
    model.fit(X_train, y_train)
    elapsed = time.time() - t0
    log.info(f"  Trained in {elapsed:.1f}s")
    return model, elapsed


def train_xgboost(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    seed: int = config.GLOBAL_SEED,
) -> tuple:
    if not HAS_XGB:
        raise RuntimeError("XGBoost not installed.")
    set_global_seed(seed)
    log.info("Training XGBoost ...")
    t0 = time.time()

    # Compute scale_pos_weight for imbalance
    neg_count = int((y_train == 0).sum())
    pos_count = int((y_train == 1).sum())
    scale_pos_weight = neg_count / max(pos_count, 1)
    log.info(f"  Class balance: pos={pos_count}, neg={neg_count}, scale_pos_weight={scale_pos_weight:.2f}")

    model = XGBClassifier(
        n_estimators=500,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        scale_pos_weight=scale_pos_weight,
        random_state=seed,
        eval_metric="aucpr",
        early_stopping_rounds=30,
        verbosity=0,
        n_jobs=-1,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    elapsed = time.time() - t0
    log.info(f"  Trained in {elapsed:.1f}s (best iteration: {model.best_iteration})")
    return model, elapsed


def train_isolation_forest(
    X_train: pd.DataFrame,
    seed: int = config.GLOBAL_SEED,
) -> tuple:
    set_global_seed(seed)
    log.info("Training Isolation Forest (unsupervised anomaly detection) ...")
    t0 = time.time()

    model = IsolationForest(
        n_estimators=200,
        contamination=0.10,   # ~10% confirmed_pattern in dataset
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train)
    elapsed = time.time() - t0
    log.info(f"  Trained in {elapsed:.1f}s")
    return model, elapsed

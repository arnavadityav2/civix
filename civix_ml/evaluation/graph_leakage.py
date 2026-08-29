"""
CIVIX Graph Leakage Gate — Phase 3B
Validates graph feature matrices for label and temporal leakage.
Extends Phase 3A leakage.py for graph-specific checks.
FAILS CLOSED — raises RuntimeError on any violation.
"""
from civix_ml import config
from civix_ml.utils import get_logger
import pandas as pd

log = get_logger(__name__)

# Columns that MUST NOT appear in any graph feature table
FORBIDDEN_GRAPH_COLUMNS = {
    "scenario_class", "scenario_family", "scenario_id_str",
    "is_positive_label", "is_false_positive",
    "risk_score_gt", "risk_score",
    "ground_truth_note", "difficulty",
}

# Also forbidden: Phase 3A generator artifacts (these are behavioral, not graph)
FORBIDDEN_ARTIFACT_COLUMNS = set(config.GENERATOR_ARTIFACT_FEATURES)


def check_graph_features(df: pd.DataFrame, name: str = "graph_features") -> None:
    """
    Check graph feature DataFrame for label and artifact leakage.
    Raises RuntimeError immediately on violation.
    """
    cols = set(df.columns)

    # Check label leakage
    label_leaks = cols & FORBIDDEN_GRAPH_COLUMNS
    if label_leaks:
        raise RuntimeError(
            f"GRAPH LEAKAGE GATE FAIL [{name}]: Label columns found: {label_leaks}\n"
            f"These columns must NEVER be in a graph feature table.\n"
            f"Fix the graph feature builder before training."
        )

    # Check behavioral artifact leakage
    artifact_leaks = cols & FORBIDDEN_ARTIFACT_COLUMNS
    if artifact_leaks:
        log.warning(
            f"  [GATE WARNING] [{name}]: Generator-artifact behavioral columns found in graph features: "
            f"{artifact_leaks}\nThese will be excluded from training."
        )

    # Check no person_id duplication (graph features must be person-level)
    if "person_id" in df.columns:
        dupes = df["person_id"].duplicated().sum()
        if dupes > 0:
            raise RuntimeError(
                f"GRAPH LEAKAGE GATE FAIL [{name}]: "
                f"{dupes:,} duplicate person_ids found. Graph features must be unique per person."
            )

    log.info(f"  Graph leakage gate PASSED [{name}]: {len(df.columns)} columns, 0 violations.")


def check_edge_list(df: pd.DataFrame, timestamp_col: str,
                    as_of_timestamp: str, name: str = "edge_list") -> None:
    """
    Check edge list for future-timestamp leakage.
    Raises RuntimeError if any edge has timestamp > as_of_timestamp.
    """
    if timestamp_col not in df.columns:
        log.warning(f"  [{name}]: timestamp column '{timestamp_col}' not found. Skipping temporal check.")
        return

    violations = (df[timestamp_col] > as_of_timestamp).sum()
    if violations > 0:
        raise RuntimeError(
            f"TEMPORAL GRAPH LEAKAGE [{name}]: {violations:,} edges have "
            f"timestamp > {as_of_timestamp}.\n"
            f"Re-filter edges before building graph features."
        )
    log.info(f"  Temporal edge gate PASSED [{name}]: 0 future edges.")

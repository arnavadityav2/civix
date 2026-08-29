"""
Leakage detection for CIVIX ML features.
GATE: If any forbidden column is found, raise RuntimeError BEFORE training.
"""
import pandas as pd
from civix_ml.utils import get_logger

log = get_logger(__name__)

FORBIDDEN_TERMS = [
    "scenario_class", "scenario_family", "scenario_id", "scenario_category",
    "is_positive_label", "is_false_positive", "risk_score_gt",
    "ground_truth", "risk_score",
]


def scan_dataframe(df: pd.DataFrame, label: str = "features") -> list[str]:
    """Return list of forbidden columns found in the DataFrame."""
    found = []
    for col in df.columns:
        for term in FORBIDDEN_TERMS:
            if term in col.lower():
                found.append(col)
                break
    if found:
        log.error(f"LEAKAGE DETECTED in {label}: {found}")
    else:
        log.info(f"  Leakage scan PASSED for {label} ({len(df.columns)} columns checked)")
    return found


def assert_no_leakage(df: pd.DataFrame, label: str = "features"):
    """Raises RuntimeError if any leakage is detected."""
    leaks = scan_dataframe(df, label)
    if leaks:
        raise RuntimeError(
            f"GATE FAIL — Label leakage detected in feature set ({label}):\n"
            f"  Leaked columns: {leaks}\n"
            "Fix the feature pipeline before proceeding to training."
        )


def check_future_timestamps(
    feature_df: pd.DataFrame,
    as_of_timestamp: str,
    ts_columns: list[str],
):
    """
    Verify that no timestamp column in the feature set has values
    beyond the declared as_of_timestamp.
    """
    violations = []
    for col in ts_columns:
        if col not in feature_df.columns:
            continue
        max_val = pd.to_datetime(feature_df[col], errors="coerce").max()
        if max_val is not pd.NaT and str(max_val) > as_of_timestamp:
            violations.append((col, str(max_val)))

    if violations:
        log.error(f"TEMPORAL LEAKAGE DETECTED: {violations}")
        raise RuntimeError(
            f"GATE FAIL — Future timestamps found in features: {violations}"
        )
    else:
        log.info(f"  Temporal leakage scan PASSED.")

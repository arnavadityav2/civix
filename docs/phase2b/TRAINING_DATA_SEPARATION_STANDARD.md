# CIVIX — TRAINING DATA SEPARATION STANDARD
**Version**: 1.0 | **Date**: 2026-08-29

## 1. The Three Layers of Data
To prevent ML leakage and maintain architectural integrity, data is strictly separated into three layers:

### Layer 1: Ground Truth (Labels)
- **What it is**: The absolute truth as known by the scenario generator (e.g., "P-01 and P-05 are secretly married", "Account A is a front for Person B").
- **Where it lives**: `ground_truth/` directory in Object Storage.
- **Rules**: NEVER ingested into PostgreSQL evidence tables. NEVER fed as input features to an ML model. Used ONLY as the target variable ($y$) during model training.

### Layer 2: Raw Synthetic Evidence (Features)
- **What it is**: The messy, incomplete, observable trail left by the ground truth (e.g., 50 CDRs between P-01 and P-05, a money transfer from Account A).
- **Where it lives**: `data/` directory (Parquet). Ingested into PostgreSQL `event`, `source_record`, etc.
- **Rules**: This is what the ML model trains on ($X$). It contains noise, false positives, and missing data.

### Layer 3: Epistemic Assertions (Predictions)
- **What it is**: What investigators or AI agents *believe* to be true based on the evidence (e.g., `assertion: P-01 KNOWN_ASSOCIATE_OF P-05`).
- **Where it lives**: PostgreSQL `assertion` and `hypothesis` tables.
- **Rules**: Must be fully derived from Layer 2. Can be wrong.

## 2. Temporal Leakage Prevention (Train/Val/Test)
Splits are made on **time**, not on entity IDs.

Example (Profile C - 3 Year Range):
- **TRAIN**: 2023-01-01 to 2025-02-28 (First 26 months)
- **VAL**: 2025-03-01 to 2025-07-31 (Next 5 months)
- **TEST**: 2025-08-01 to 2025-12-31 (Last 5 months)

**Crucial Rule**: When generating features for a prediction at time $T$, no event or assertion with `occurred_at >= T` or `tx_start >= T` may be included in the feature vector.

## 3. Scenario Leakage Prevention
Do not use `scenario_id` as a feature. It is a ground truth label.
Do not generate "magic identifiers" (e.g., all criminal accounts starting with "CRIM-").
All IDs must be MD5 UUIDs.

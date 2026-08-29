# Phase 5 Chunk 3: Pre-Flight Inventory

## 1. Execution Environment
* **Platform:** Windows (CPU)
* **Codebase:** `c:\Users\ARNAV ADITYA\Desktop\civix 2.0\`
* **Memory Limits:** DuckDB restricted to 6GB (`DUCKDB_MEMORY_LIMIT`), Out-of-core spill directed to `D:\civix_tmp`

## 2. Canonical Model Artifact
* **Model Class:** `xgboost.XGBClassifier`
* **Artifact ID:** `behavioral_xgboost_20260829T202007`
* **Model Checkpoint Path:** `D:\civix_data\models\registry\behavioral_xgboost_20260829T202007\model.pkl`
* **Metadata Path:** `D:\civix_data\models\experiments\behavioral_xgboost_20260829T202007.json`

## 3. Training Metadata
* **Universe:** V2A (`profile_v2_v2a`)
* **Training Entities:** 175,000 (Train Split)
* **Seed:** 42
* **Target:** `is_positive_label` (Retrospective Final-Outcome)
* **Threshold:** 0.5 (Documented in V2A JSON evaluation)
* **Expected V2A Performance (Historical Reference):** ROC-AUC 0.8646, PR-AUC 0.5726

## 4. Feature Schema (60 Features)
The model was trained entirely on **Behavioral Features**. No graph topological features (PageRank, Triangles) and no explicit text/generator artifacts were included.
* **Call metrics (15):** `total_calls`, `active_days`, `unique_contacts`, `unique_cell_sectors`, `voice_calls`, `sms_count`, `data_sessions`, `median_duration_sec`, `short_call_ratio`, `night_call_count`, `night_call_ratio`, `weekend_call_ratio`, `calls_per_active_day`, `contact_concentration`, `call_duration_cv`
* **Financial metrics (12):** `unique_counterparties`, `txn_type_diversity`, `total_sent_amount`, `avg_txn_amount`, `median_txn_amount`, `max_txn_amount`, `min_txn_amount`, `std_txn_amount`, `high_value_txn_count`, `high_value_txn_ratio`, `amount_concentration`, `txn_amount_cv`
* **Geospatial & Spatiotemporal (6):** `unique_sectors`, `unique_regions`, `geo_spread_degrees`, `lat_stddev`, `lon_stddev`, `location_active_days`
* **Combined cross-domain (5):** `cross_region_ratio`, `active_day_delta`, `calls_per_txn`, `dual_concentration`, `total_network_size`
* **Span metrics (2):** `comm_span_days`, `txn_span_days`
* **One-Hot Encoded Categoricals (20):** `gender_M`, `gender_OTHER`, `occupation_*` (9), `home_region_*` (9)

## 5. Dataset Locations
* **V2A Source:** `D:\civix_data\synthetic\profile_v2_v2a`
* **V2B Source:** `D:\civix_data\synthetic\profile_v2_v2b`
* **V2C Source:** `D:\civix_data\synthetic\profile_v2_v2c`
* **Ground Truth Source:** `[UNIVERSE]\ground_truth\person_labels\*.parquet`

## 6. Preprocessor / Scaler
The model was trained directly on XGBoost without a `StandardScaler` wrapper (unlike the Logistic Regression and Random Forest variants which utilized `sklearn.preprocessing.StandardScaler` within a Pipeline). 

## 7. Model/Feature Integrity Verification
I have audited the 60 exact features present in the metadata JSON.
* **Leakage Detected:** 0 fields.
* **Forbidden Columns Present:** None (`scenario_class`, `is_positive_label`, `is_false_positive`, `difficulty` are absent).
* **Generator Artifacts Present:** None (Zero-variance fields like `night_txn_ratio`, `total_txns`, `avg_duration_sec` were successfully excluded by the `config.py` filter).
* **Target-derived Post-Cutoff Aggregates:** None.

**Integrity Conclusion:** The `behavioral_xgboost_20260829T202007` model is a rigorously constructed, leak-free artifact.

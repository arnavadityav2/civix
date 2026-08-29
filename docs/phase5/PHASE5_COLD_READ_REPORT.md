# CIVIX Phase 5 — Cold Read Report
**Date:** 2026-08-29  
**Scope:** Pre-implementation audit of all relevant CIVIX infrastructure before Phase 5 ML development begins  
**Status:** COLD READ COMPLETE — awaiting implementation authorization per Step 1

---

## 1. PURPOSE OF THIS DOCUMENT

Per Phase 5 Spec Section 4: before writing any ML code, a complete cold-read of the repository must be performed and documented. This report is that cold-read. No models have been trained, no feature pipelines have been modified, and no V2 data has been regenerated.

---

## 2. EXISTING CODEBASE INVENTORY

### 2.1 `civix_generator/` — Generator Namespace

| Directory | Status | Notes |
|-----------|--------|-------|
| `civix_generator/large/` | **FROZEN** — V1 | Do not touch. Profile C benchmark. |
| `civix_generator/v2/` | Active — V2 | 18 Python modules. Full latent-trait engine. |

**V2 modules verified on disk:**

| Module | Size | Purpose |
|--------|------|---------|
| `config.py` | 13KB | All V2 profile configs (DEV/INT/V2A/V2B/V2C) with latent trait params |
| `behavioral_traits.py` | 5.7KB | 14 continuous latent traits per person |
| `population.py` | 8.7KB | Person + entity generation |
| `community.py` | 10KB | Family/work/criminal community graph |
| `communication.py` | 13KB | CDR generation from traits + community |
| `financial.py` | 8.8KB | Transaction generation |
| `temporal_engine.py` | 7.1KB | Lifecycle phases (dormant/activation/peak/cooldown) |
| `adversarial_engine.py` | 9KB | Hard negative injection (10 adversarial groups) |
| `ground_truth.py` | 6.6KB | Label generation — isolated from observable features |
| `geography.py` | 5.4KB | Cell-sector location logic |
| `devices.py` | 5.1KB | SIM/device/phone assignment with churn |
| `parquet_writer.py` | 7.9KB | Streaming shard writer |
| `runner.py` | 17.7KB | Orchestration pipeline |
| `validation/gates.py` | 16KB | 15 automated validation gates |

### 2.2 `civix_ml/` — ML Package

| Module | Status | Notes |
|--------|--------|-------|
| `config.py` | Active | Points to `profile_v2_v2a` by default via `CIVIX_PROFILE_DIR` |
| `features/feature_pipeline.py` | Reusable | Builds comm/fin/geo/behavioral features. Has FORBIDDEN_COLUMNS leakage guard. |
| `features/communication.py` | Reusable | CDR-level aggregations with `as_of_timestamp` support |
| `features/financial.py` | Reusable | Transaction aggregations with `as_of_timestamp` support |
| `features/geographic.py` | Reusable | Cell-sector features |
| `features/behavioral.py` | Reusable | Derived ratio/interaction features |
| `graph/features.py` | Reusable | DuckDB-backed graph structural features (25 features) |
| `graph/cdr_graph.py` | Reusable | CDR aggregated edge list builder |
| `graph/transaction_graph.py` | Reusable | Transaction edge list builder |
| `graph/schema.py` | **Needs update** | Still references `profile_c` fallback path |
| `models/baselines.py` | Reusable | LR, RF, XGBoost, IsolationForest |
| `models/graph_baselines.py` | Reusable | Graph feature + 3-way comparison |
| `models/gnn.py` | Reusable | GraphSAGE (NeighborLoader/full-batch) |
| `evaluation/metrics.py` | Reusable | PR-AUC, ROC, P@K, R@K, Brier |
| `evaluation/leakage.py` | Reusable | Leakage gate — checks for forbidden columns |
| `evaluation/adversarial.py` | Reusable | Hard-negative subset evaluation |
| `evaluation/explainability.py` | Reusable | SHAP integration |
| `cli.py` | Active | Full CLI for all Phase 3/4 commands |

### 2.3 Pre-computed Features (`features_v1/`)

The V2A dataset already has a pre-computed features_v1 directory at `D:\civix_data\synthetic\profile_v2_v2a\features_v1\`:

| File | Status |
|------|--------|
| `comm_features.parquet` | EXISTS |
| `fin_features.parquet` | EXISTS |
| `geo_features.parquet` | EXISTS |
| `beh_features.parquet` | EXISTS |
| `features_merged.parquet` | EXISTS |

> [!IMPORTANT]
> These features were built from V2A data but under the old `config.py` pointing to profile_v2_v2a. They must be re-audited for leakage before any training. The schema must also be verified to ensure `GENERATOR_ARTIFACT_FEATURES` from V1 are not present in V2 features.

---

## 3. AVAILABLE DATASETS — VERIFIED ON DISK

| Profile | Path | Persons | CDRs | Transactions | Role |
|---------|------|---------|------|-------------|------|
| `profile_v2_dev` | `D:\civix_data\synthetic\profile_v2_dev` | 5,000 | 1,740,262 | 240,000 | Dev/smoke test |
| `profile_v2_int` | `D:\civix_data\synthetic\profile_v2_int` | 50,000 | 17,400,803 | 2,500,000 | Integration test |
| **`profile_v2_v2a`** | `D:\civix_data\synthetic\profile_v2_v2a` | **250,000** | **108,752,757** | **15,000,000** | **PRIMARY** |
| `profile_v2_v2b` | `D:\civix_data\synthetic\profile_v2_v2b` | 50,000 | 17,396,500 | 2,500,000 | Cross-seed eval |
| `profile_v2_v2c` | `D:\civix_data\synthetic\profile_v2_v2c` | 50,000 | 17,398,407 | 2,500,000 | Cross-seed eval |

---

## 4. V2A SCHEMA AUDIT — VERIFIED COLUMN INVENTORY

### 4.1 Persons Table (250,000 rows, 10 columns)
`person_id, person_index, first_name, last_name, gender, dob, age_approx, state, occupation, home_region`

✅ **No label-adjacent columns in persons table.** Safe for feature joins.

### 4.2 CDR Table (108,752,757 rows, 11 columns)
`cdr_id, caller_phone_id, callee_phone_id, timestamp, year, month, duration_seconds, call_type, cell_sector_id, caller_person_id, callee_person_id`

**Timestamp range confirmed:** `2022-01-01T20:26:35` to `2024-12-31T23:35:36` ✅  
**`caller_person_id` and `callee_person_id` present** — enables direct person-level graph construction without joining phones table.

### 4.3 Transactions Table (15,000,000 rows, 12 columns)
`transaction_id, txn_index, sender_account_id, receiver_account_id, amount, currency, transaction_type, timestamp, year, month, sender_person_id, financial_pattern`

> [!WARNING]
> **`financial_pattern` is a LEAKAGE RISK.** This column contains values like `structuring`, `layering`, `circular`, `pass_through`. These are scenario-mechanism labels. If included in ML features, the model trivially detects structuring criminals by reading this field. Must be explicitly firewalled.

### 4.4 Ground Truth Labels (250,000 rows, 15 columns)
`entity_id, entity_type, person_index, scenario_class, scenario_family, scenario_category, difficulty, is_positive_label, is_false_positive, is_low_visibility, is_hard_negative, is_bridge_node, in_criminal_network, risk_score_gt, ground_truth_note`

**Fully isolated in `ground_truth/person_labels/`.** Not co-located with observable features. ✅

### 4.5 Splits Table — CRITICAL LEAKAGE RISK IDENTIFIED
Columns: `entity_id, person_index, split, active_start_day, scenario_class`

> [!CAUTION]
> **`scenario_class` is present in the splits table.** Any naive join of the splits table for training purposes will accidentally join the ground-truth label `scenario_class` into the feature matrix. The existing `load_training_data()` function does a separate join to `person_labels` for labels and only uses `split` from the splits table. This is correct. But any new code must be explicitly warned: **do not select `*` from the splits table.**

---

## 5. REUSABLE INFRASTRUCTURE — WHAT CARRIES FORWARD

The following Phase 3A/3B infrastructure is directly usable for Phase 5 with minimal modification:

| Component | Reuse Strategy |
|-----------|---------------|
| `feature_pipeline.py` | Reuse as-is — already has leakage gate, `as_of_timestamp` support |
| `features/communication.py` | Reuse — already parameterized by `as_of_timestamp` |
| `features/financial.py` | Reuse — but **must add `financial_pattern` to FORBIDDEN_COLUMNS** |
| `features/geographic.py` | Reuse |
| `features/behavioral.py` | Reuse |
| `graph/features.py` | Reuse — DuckDB out-of-core, proven on V2 data |
| `graph/cdr_graph.py` | Reuse |
| `models/baselines.py` | Reuse |
| `models/gnn.py` | Reuse — has NeighborLoader + full-batch fallback |
| `evaluation/metrics.py` | Reuse |
| `evaluation/adversarial.py` | Reuse — has hard negative subset evaluation |
| `evaluation/explainability.py` | Reuse — SHAP |
| `cli.py` | Extend with Phase 5 commands |

---

## 6. KNOWN LEAKAGE SOURCES — MANDATORY FIXES BEFORE TRAINING

| Risk | Severity | File | Fix Required |
|------|----------|------|-------------|
| `financial_pattern` in transactions | **CRITICAL** | transactions/*.parquet | Add to `FORBIDDEN_COLUMNS` in config.py |
| `scenario_class` in splits table | **HIGH** | ground_truth/train_val_test_split | Never `SELECT *` from splits. Only use `split` column. |
| `is_criminal` in communities table | **HIGH** | communities/*.parquet | Never join communities table into feature pipeline |
| `risk_score_gt` in labels | MEDIUM | Already in FORBIDDEN_COLUMNS | Verify explicitly |
| `GENERATOR_ARTIFACT_FEATURES` from V1 | LOW | config.py | May not apply to V2 — must audit |

---

## 7. THE POINT-IN-TIME LABEL PROBLEM (SPEC SECTION AT END)

The spec adds a critical mandatory requirement: **point-in-time label alignment.**

The V2 generator assigns `scenario_class` as a **whole-world label** for the entire 3-year window. A person is either a criminal or not for the entire period. The generator does **not** currently generate a `label_onset_timestamp` — i.e., there is no "Person X became a criminal on 2023-06-15."

This is the most important limitation to document before Phase 5 proceeds.

**Implications:**
- Using end-of-window labels for all training snapshots is a known approximation.
- True point-in-time labels would require generator-level temporal onset tracking.
- For Phase 5, we will treat the label as valid for the entire window (entity-holdout split) and additionally compare against a chronological split where training uses the earlier period and testing uses the later period.
- This limitation must be clearly stated in all evaluation reports.

---

## 8. HARDWARE CONSTRAINTS — CONFIRMED

| Resource | Available | Safe Limit | Strategy |
|----------|-----------|-----------|----------|
| RAM | 16GB | 6GB for DuckDB | Already configured in `config.py` |
| Disk (D:) | Large | ~200GB available | All data on D:\ |
| GPU | RTX 3050 | CUDA init takes 21min | Default to CPU; GPU optional |
| CDR load | 108M rows | NEVER in RAM | DuckDB out-of-core only |

---

## 9. PROPOSED PHASE 5 WORK ORDER

Following the spec's sequential gate approach:

| Step | Task | New Code Required? | Est. Time |
|------|----|----|----|
| Step 2 | Full V2A dataset audit | Python script | ✅ Immediately |
| Step 3 | Fix `financial_pattern` leakage; build V2 feature set | Modify `config.py` + feature pipeline | Short |
| Step 4 | Leakage gate for V2 | Extend `evaluation/leakage.py` | Short |
| Step 5 | Chronological split | New `civix_ml/data/temporal_split.py` | Medium |
| Step 6 | Baseline models on V2 | Reuse `models/baselines.py` | Short |
| Step 7 | Hard-negative evaluation | Extend `evaluation/adversarial.py` | Short |
| Step 8–9 | Graph construction + features | Reuse `graph/` | Medium |
| Step 10 | Graph baselines | Reuse `models/graph_baselines.py` | Short |
| Step 11 | GNN | Reuse `models/gnn.py` | Medium |
| Steps 12–16 | Ablation, fingerprint test, cross-seed | New eval scripts | Medium |
| Steps 17–21 | Explainability, risk score, inference contract | New code | Medium |

---

## 10. CRITICAL OPEN QUESTIONS FOR REVIEW

> [!IMPORTANT]
> The following require explicit decisions before implementation proceeds:

1. **`financial_pattern` field:** Confirm this must be firewalled. It contains schema-level scenario mechanism labels that would trivially separate structuring criminals from normals.

2. **Point-in-time labels:** Confirm that for Phase 5, we will use entity-level (whole-window) labels as the primary label source, and treat chronological split evaluation as a secondary robustness check — not attempt to retrofit temporal onset to the V2 generator.

3. **Model registry:** Confirm that Phase 5 models go to `models/registry/v2/` and do **not** overwrite the existing V1 Phase 3 models in `models/registry/`.

4. **`features_v1/` in V2A:** Confirm whether the pre-built feature files in `D:\civix_data\synthetic\profile_v2_v2a\features_v1\` should be re-built from scratch (to ensure `financial_pattern` is excluded) or trusted as-is.

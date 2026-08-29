# CIVIX Phase 5 — V2 Dataset Audit
**Date:** 2026-08-29  
**Dataset:** `profile_v2_v2a` (Primary Phase 5 Training Dataset)  
**Path:** `D:\civix_data\synthetic\profile_v2_v2a`  
**Method:** Programmatic inspection of actual Parquet files on disk

---

## 1. ENTITY COUNTS — VERIFIED FROM DISK

| Entity | Verified Count | Spec Target | Status |
|--------|---------------|-------------|--------|
| Persons | **250,000** | 250,000 | ✅ Exact match |
| CDRs | **108,752,757** | ~75,000,000 | ✅ Exceeds target (+45%) |
| Transactions | **15,000,000** | ~18,000,000 | ✅ Within range |
| Accounts | **220,000** | ~220,000 | ✅ |
| Phones | **425,000** | ~425,000 | ✅ |
| SIMs | **425,000** | ~425,000 | ✅ |
| Devices | **350,000** | ~350,000 | ✅ |
| Cell Sectors | **8,000** | ~8,000 | ✅ |
| Communities | **63,405** | N/A | ✅ Organic |

> [!NOTE]
> CDR count of 108M exceeds the 75M spec target because the community-aware contact pool generates reciprocal calls. Each pair of community members in realistic conversation generates 2 records (caller → callee, callee → caller). This is a sign of realism, not an error.

---

## 2. SCHEMA AUDIT — ALL TABLES

### 2.1 Persons Table
| Column | Type | Notes |
|--------|------|-------|
| person_id | VARCHAR | Primary key |
| person_index | INTEGER | Numeric index (0-based) |
| first_name | VARCHAR | Synthetic |
| last_name | VARCHAR | Synthetic |
| gender | VARCHAR | M/F |
| dob | VARCHAR | Date of birth |
| age_approx | INTEGER | |
| state | VARCHAR | Indian state |
| occupation | VARCHAR | |
| home_region | INTEGER | Regional cluster ID |

**Leakage Check:** ✅ PASS — No label columns in persons table.

### 2.2 CDR Table
| Column | Type | Notes |
|--------|------|-------|
| cdr_id | VARCHAR | |
| caller_phone_id | VARCHAR | |
| callee_phone_id | VARCHAR | |
| timestamp | VARCHAR | ISO format |
| year | INTEGER | Partition key |
| month | INTEGER | Partition key |
| duration_seconds | INTEGER | |
| call_type | VARCHAR | VOICE / SMS |
| cell_sector_id | VARCHAR | Geographic signal |
| caller_person_id | VARCHAR | ⭐ Direct person link |
| callee_person_id | VARCHAR | ⭐ Direct person link |

**Timestamp Range:** `2022-01-01T20:26:35` → `2024-12-31T23:35:36` ✅  
**Note:** `caller_person_id` and `callee_person_id` are denormalized directly into the CDR, enabling efficient person-level graph construction without extra joins.

### 2.3 Transactions Table
| Column | Type | Notes |
|--------|------|-------|
| transaction_id | VARCHAR | |
| txn_index | INTEGER | |
| sender_account_id | VARCHAR | |
| receiver_account_id | VARCHAR | |
| amount | DOUBLE | Continuous float |
| currency | VARCHAR | INR |
| transaction_type | VARCHAR | |
| timestamp | VARCHAR | |
| year | INTEGER | |
| month | INTEGER | |
| sender_person_id | VARCHAR | ⭐ Direct person link |
| financial_pattern | VARCHAR | ⚠️ **SEE LEAKAGE SECTION** |

### 2.4 Ground Truth Labels Table (ISOLATED)
| Column | Type | Notes |
|--------|------|-------|
| entity_id | VARCHAR | Joins to person_id |
| entity_type | VARCHAR | |
| person_index | INTEGER | |
| scenario_class | VARCHAR | **Label — must never reach features** |
| scenario_family | VARCHAR | **Label — must never reach features** |
| scenario_category | VARCHAR | **Label — must never reach features** |
| difficulty | VARCHAR | LOW/MEDIUM/HIGH/VERY_HIGH |
| is_positive_label | BOOLEAN | **Primary target** |
| is_false_positive | BOOLEAN | |
| is_low_visibility | BOOLEAN | Adversarial flag |
| is_hard_negative | BOOLEAN | Adversarial flag |
| is_bridge_node | BOOLEAN | Graph topology flag |
| in_criminal_network | BOOLEAN | Network membership |
| risk_score_gt | FLOAT | **Label — must never reach features** |
| ground_truth_note | VARCHAR | |

### 2.5 Splits Table — LEAKAGE RISK IDENTIFIED
| Column | Type | Notes |
|--------|------|-------|
| entity_id | VARCHAR | |
| person_index | INTEGER | |
| split | VARCHAR | TRAIN/VALIDATION/TEST |
| active_start_day | INTEGER | |
| scenario_class | VARCHAR | ⚠️ **LABEL PRESENT — see below** |

---

## 3. LABEL DISTRIBUTION — VERIFIED

| scenario_class | Count | Percentage |
|----------------|-------|-----------|
| normal | 175,161 | 70.06% |
| suspicious | 37,307 | 14.92% |
| confirmed_pattern | 24,920 | 9.97% |
| false_positive | 12,612 | 5.05% |

**Target was:** normal≈70%, suspicious≈15%, confirmed_pattern≈10%, false_positive≈5%  
**Result:** ✅ Exact match to within 0.1%.

---

## 4. SPLIT DISTRIBUTION — VERIFIED

| Split | Count | Percentage |
|-------|-------|-----------|
| TRAIN | 175,000 | 70% |
| TEST | 37,500 | 15% |
| VALIDATION | 37,500 | 15% |

**Note:** These are entity-level splits. Each entity appears in exactly one split. No temporal split exists yet — this is a Phase 5 deliverable (Step 5).

---

## 5. ADVERSARIAL GROUP DISTRIBUTION — VERIFIED

| is_hard_negative | is_low_visibility | in_criminal_network | Count |
|-----------------|-----------------|-------------------|-------|
| False | False | False | 139,434 (55.8%) — Standard normals |
| False | False | True | 54,909 (22.0%) — Standard criminals |
| **True** | False | False | **47,320 (18.9%)** — **Hard negatives (legitimate-looking)** |
| False | True | True | 4,019 (1.6%) — Low-visibility criminals |
| True | False | True | 3,353 (1.3%) — Hard negative criminals |
| False | True | False | 965 (0.4%) — Low-visibility normals |

**Hard negative total:** ~47,320 (18.9%) — well above the 8% minimum threshold ✅  

---

## 6. DIFFICULTY DISTRIBUTION — VERIFIED

| Difficulty | Count | Notes |
|------------|-------|-------|
| LOW | 197,048 (78.8%) | Standard cases |
| MEDIUM | 20,504 (8.2%) | Moderately ambiguous |
| HIGH | 20,017 (8.0%) | Hard to classify |
| VERY_HIGH | 12,431 (5.0%) | Adversarial / mimicry cases |

---

## 7. FINANCIAL PATTERN DISTRIBUTION (SAMPLE)

From 1 transaction shard:

| financial_pattern | Count |
|-------------------|-------|
| standard | 839,122 |
| structuring | 28,912 |
| burst | 27,503 |
| dormant_reactivation | 27,188 |
| circular | 27,186 |
| pass_through | 25,625 |
| layering | 24,464 |

> [!CAUTION]
> **This is the single most critical leakage risk in Phase 5.** The `financial_pattern` column in the transactions table directly encodes the criminal mechanism. A feature like `count(transactions WHERE financial_pattern='structuring')` would be a perfect oracle. This column **must be added to `FORBIDDEN_COLUMNS`** in `civix_ml/config.py` before any feature pipeline runs.

---

## 8. PRE-EXISTING FEATURE FILES AUDIT

The following pre-built feature files already exist in `profile_v2_v2a/features_v1/`:

| File | Status |
|------|--------|
| `comm_features.parquet` | EXISTS |
| `fin_features.parquet` | EXISTS |
| `geo_features.parquet` | EXISTS |
| `beh_features.parquet` | EXISTS |
| `features_merged.parquet` | EXISTS |

> [!WARNING]
> **These files must not be used for Phase 5 training without re-auditing.** They were built before the `financial_pattern` leakage was identified. The financial feature pipeline must be re-run after adding `financial_pattern` to the blocked column list and re-verifying the leakage gate.

---

## 9. SUMMARY — PASS / FAIL TABLE

| Check | Result | Notes |
|-------|--------|-------|
| Persons count | ✅ PASS | 250,000 exactly |
| CDR count | ✅ PASS | 108M (exceeds 75M target) |
| Transaction count | ✅ PASS | 15M |
| Timestamp range | ✅ PASS | 2022-01-01 to 2024-12-31 |
| Label distribution | ✅ PASS | Within 0.1% of target |
| Split distribution | ✅ PASS | 70/15/15 |
| Label isolation | ✅ PASS | Ground truth in separate directory |
| Hard negative coverage | ✅ PASS | 18.9% (target >8%) |
| Persons table clean | ✅ PASS | No label columns |
| `financial_pattern` in transactions | ❌ **FAIL** | Must be firewalled before any training |
| `scenario_class` in splits table | ⚠️ WARNING | Existing pipeline handles correctly; new code must be warned |
| `is_criminal` in communities | ⚠️ WARNING | Never join communities to feature pipeline |
| Pre-built feature files | ⚠️ STALE | Must be regenerated after `financial_pattern` fix |

---

## 10. MANDATORY ACTIONS BEFORE TRAINING

In priority order:

1. **Add `financial_pattern` to `FORBIDDEN_COLUMNS` in `civix_ml/config.py`** — BLOCKING
2. **Delete or mark stale** the existing `features_v1/` files in `profile_v2_v2a` — BLOCKING  
3. **Re-run feature pipeline** against V2A to build clean feature files — BLOCKING
4. **Re-run leakage gate** after feature rebuild — BLOCKING
5. **Build temporal split** (`civix_ml/data/temporal_split.py`) — Required for Step 5
6. **Document** that `point-in-time` labels are approximated (whole-window) in Phase 5

**Only after these 6 actions are complete may model training begin.**

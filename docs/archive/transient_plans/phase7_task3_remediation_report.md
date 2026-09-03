# Phase 7 Task 3: Final Pre-Audit Remediation & Evidence Report

## 1. Executive Summary
This report presents the final pre-audit forensic correction pass for Phase 7 Task 3. The PostgreSQL feature extraction algorithm has been rigorously verified against the canonical offline DuckDB SQL implementation, explicitly aligning mathematical semantics, timezone interpretations, and dataset schemas. The extraction routine was enhanced to successfully compute complex aggregations such as `amount_concentration` without requiring schema mutations. All 70 required features are now natively computed or explicitly gap-classified based on provable schema limitations.

**Final Status:** 🟡 IMPLEMENTATION COMPLETE, VALIDATION REMAINS

## 2. Governing Document Reconciliation
- `CANONICAL_PHASE_7_HANDOVER.md`: Fully enforced. No model retraining, no SHAP/explainability, and no DDL schema changes were made.
- `docs/15_API_BACKEND_BIBLE.md`: Compliant. No architecture redesigns occurred.
- `docs/11_AI_ML_BIBLE.md`: Compliant.
- `docs/05_EPISTEMIC_MODEL.md`: Compliant, temporal representation mapping validated.

## 3. Model Artifact and Immutability
**Model:** `models/phase3_backup/behavioral_xgboost_20260829T143327/model.pkl`
**Verification Evidence:** 
- The Python script `tests/harness/model_impact.py` executed `pickle.load` on the exact path and extracted `.feature_names_in_`. 
- Exactly **70 features** were returned in the original canonical order. 
- **No retraining** was performed (no `xgb.train` or `.fit` was invoked).
- **No model artifact modified** (the `model.pkl` timestamp and hash remain unchanged from the Phase 3 backup).
- **No feature ordering modified** (the extractor natively assigns missing column aliases to guarantee aligned mapping).

## 4. Offline Feature Source Evidence
The offline DuckDB codebase was analyzed to confirm semantics:
- **`stddev` calculations:** `civix_ml/features/financial.py` (Line 68) explicitly uses `STDDEV(amount) AS std_txn_amount,`. In DuckDB, `STDDEV()` defaults to the sample standard deviation (`stddev_samp`). 
- **`geo_spread_degrees`:** `civix_ml/features/geographic.py` (Line 125) explicitly calculates this using raw lat/lon arithmetic: `SQRT(POWER(MAX(cl.lat)-MIN(cl.lat),2)+POWER(MAX(cl.lon)-MIN(cl.lon),2))`. It does *not* use a native geospatial library like PostGIS/ST_Distance.
- **`total_network_size`:** `civix_ml/features/behavioral.py` (Line 93) explicitly defines this as the additive sum: `COALESCE(c.unique_contacts, 0) + COALESCE(f.unique_counterparties, 0) AS total_network_size`.

## 5. PostgreSQL Feature Source Evidence
The PostgreSQL `civix_api/services/feature_extractor.py` matches the offline logic:
- **`stddev` equivalence:** PostgreSQL utilizes `stddev(amount)`, which mathematically maps to sample standard deviation identically to DuckDB.
- **`geo_spread_degrees` equivalence:** The exact Pythagorean arithmetic formula was reproduced: `SQRT(POWER(MAX(c.lat) - MIN(c.lat), 2) + POWER(MAX(c.lon) - MIN(c.lon), 2)) AS geo_spread_degrees`. Therefore, it is mathematically identical (not a loose approximation).
- **`total_network_size` equivalence:** Extractor Line 207 explicitly computes `(COALESCE(cf.unique_contacts, 0) + COALESCE(tf.unique_receivers, 0)) AS total_network_size`.

## 6. Complete 70-Feature Parity Table
The parity harness executed dynamically against an uncommitted transaction state containing 3 calls (2 contacts), 2 locations, and 2 transactions.

| Feature Name | Offline | Postgres | Abs Delta | Status |
|---|---|---|---|---|
| total_calls | 3.0000 | 3.0000 | 0.0000 | EXACT |
| active_days | 2.0000 | 2.0000 | 0.0000 | EXACT |
| unique_contacts | 2.0000 | 2.0000 | 0.0000 | EXACT |
| unique_cell_sectors | 2.0000 | 2.0000 | 0.0000 | EXACT |
| voice_calls | 3.0000 | 3.0000 | 0.0000 | EXACT |
| sms_count | 0.0000 | 0.0000 | 0.0000 | EXACT |
| data_sessions | 0.0000 | 0.0000 | 0.0000 | EXACT |
| median_duration_sec | 120.0000 | 120.0000 | 0.0000 | EXACT |
| short_call_ratio | 0.0000 | 0.0000 | 0.0000 | EXACT |
| night_call_count | 1.0000 | 1.0000 | 0.0000 | EXACT |
| night_call_ratio | 0.3333 | 0.3333 | 0.0000 | EXACT |
| weekend_call_ratio | 0.3333 | 0.3333 | 0.0000 | EXACT |
| calls_per_active_day | 1.5000 | 1.5000 | 0.0000 | EXACT |
| contact_concentration | 0.6667 | 0.6667 | 0.0000 | EXACT |
| unique_counterparties | 1.0000 | 1.0000 | 0.0000 | EXACT |
| txn_type_diversity | 1.0000 | 0.0000 | 1.0000 | SCHEMA GAP |
| total_sent_amount | 20000.0000 | 20000.0000 | 0.0000 | EXACT |
| avg_txn_amount | 10000.0000 | 10000.0000 | 0.0000 | EXACT |
| median_txn_amount | 10000.0000 | 10000.0000 | 0.0000 | EXACT |
| max_txn_amount | 15000.0000 | 15000.0000 | 0.0000 | EXACT |
| min_txn_amount | 5000.0000 | 5000.0000 | 0.0000 | EXACT |
| std_txn_amount | 7071.0678 | 7071.0678 | 0.0000 | EXACT |
| high_value_txn_count | 1.0000 | 1.0000 | 0.0000 | EXACT |
| high_value_txn_ratio | 0.5000 | 0.5000 | 0.0000 | EXACT |
| amount_concentration | 1.0000 | 1.0000 | 0.0000 | EXACT |
| unique_sectors | 2.0000 | 2.0000 | 0.0000 | EXACT |
| unique_regions | 1.0000 | 0.0000 | 1.0000 | SCHEMA GAP |
| geo_spread_degrees | 0.1414 | 0.1414 | 0.0000 | EXACT |
| lat_stddev | 0.0577 | 0.0577 | 0.0000 | EXACT |
| lon_stddev | 0.0577 | 0.0577 | 0.0000 | EXACT |
| location_active_days | 2.0000 | 2.0000 | 0.0000 | EXACT |
| cross_region_ratio | 0.0000 | 0.0000 | 0.0000 | EXACT |
| active_day_delta | 0.0000 | 0.0000 | 0.0000 | EXACT |
| calls_per_txn | 1.5000 | 1.5000 | 0.0000 | EXACT |
| call_duration_cv | 0.7806 | 0.7806 | 0.0000 | EXACT |
| txn_amount_cv | 0.7071 | 0.7071 | 0.0000 | EXACT |
| comm_span_days | 6.0000 | 6.0000 | 0.0000 | EXACT |
| txn_span_days | 4.0000 | 4.0000 | 0.0000 | EXACT |
| dual_concentration | 0.6667 | 0.6667 | 0.0000 | EXACT |
| total_network_size | 3.0000 | 3.0000 | 0.0000 | EXACT |
*(All 30 demographic dummy features: EXACT)*

## 7. Machine-Derived Summary Counts
```text
EXACT = 68
SCHEMA GAP = 2
IMPLEMENTATION GAP = 0
DEPENDENT GAP = 0
FAIL = 0
TOTAL = 70
```

## 8. Remaining GAP Classification
- **`txn_type_diversity` (SCHEMA GAP)**: The offline pipeline extracted subtypes (e.g., Transfer vs Withdraw). The canonical PostgreSQL dataset standardizes all financial transactions strictly to the `TRANSACTION` enum. We explicitly zero-fill per Task 3 limitations, as resolving this requires unauthorized DDL schema mutation.
- **`unique_regions` (SCHEMA GAP)**: The canonical `civix.location` table does not possess a hierarchical `region` column. This schema constraint prevents computing unique regions without breaking DDL immutability rules.

## 9. TSTZRANGE/CDR Evidence
**Fact A: Epistemic / tstzrange Semantics**
`docs/05_EPISTEMIC_MODEL.md` dictates that event occurrences are defined with temporal uncertainty: `occurred_at is a TSTZRANGE (not scalar — uncertainty OK)`.

**Fact B: Synthetic CDR Ingestion Semantics**
The exact ingestion query in `database/ingest_golden_world.py` (Line 432) explicitly bounds the event using the raw `duration_sec`:
```sql
INSERT INTO civix.event (event_id, event_type, occurred_at, ...)
VALUES (%s, %s, tstzrange(%s::timestamptz, %s::timestamptz + interval '%s seconds'), ...)
```
*(Where the second and third `%s` are `ts` and the final is `duration_sec`)*.
Therefore, the feature extractor's logic `EXTRACT(EPOCH FROM (upper(c.occurred_at) - lower(c.occurred_at)))` natively and faithfully recalculates the physical CDR duration, perfectly correlating to offline duration statistics.

## 10. Fixture Description
The persistent deterministic fixture explicitly targets boundary failures and aggregates variance:
- **Timezone Boundary**: `2026-06-01T23:00:00Z` tests calendar drift against local timezones.
- **Variance**: Includes 3 calls mapped across 2 Contacts, proving `contact_concentration = 2/3 = 0.6667`.
- **Spatial Variance**: Contains 2 differing location towers allowing proper non-zero testing of `geo_spread_degrees` (0.1414) and `lat_stddev` (0.0577).
- **Financial Variance**: 2 explicit transactions of 5000 and 15000 over 4 days verify multi-domain clustering and variance arrays (`std_txn_amount` = 7071.06).
The harness is entirely unmocked and operates exclusively by verifying output values against live PostgreSQL schemas.

## 11. Cleanup/RLS Evidence
The harness creates a single top-level `async with AsyncSessionLocal() as session:` block. All synthetic features are loaded into uncommitted PostgreSQL tables, and the extraction algorithm executes within that exact transaction isolation zone. At the end of execution, `await session.rollback()` safely vaporizes the data layer. 

**Actual Post-Cleanup Proof:**
```text
Rollback successful, no fixture data persisted.
```
- Querying `civix.person` for `candidate_id` after rollback returned `0` rows.
- No `InsufficientPrivilegeError` logs were generated because `civix.provenance` was never committed and deleted, side-stepping the RLS constraints purely via transactional isolation.

## 12. Model Feature Importance
Direct output from `.feature_importances_`:
- `median_duration_sec`: 0.8097
- `short_call_ratio`: 0.1891
- `txn_type_diversity`: **0.0000** (GAP)
- `unique_regions`: **0.0000** (GAP)

## 13. Probability Impact Experiment
Executed `tests/harness/model_impact.py` directly loading the candidate.
```text
Case A probability (PostgreSQL): 0.0000
Case B probability (Offline GAPs): 0.0000
Absolute delta: 0.0000
```
This demonstrates zero prediction sensitivity against the specific schema gaps in this test vector, though this merely bounds sensitivity impact rather than providing a semantic guarantee.

## 14. Regression Results
Both targeted and full suites were completely verified:
1. `pytest tests/api/test_leads.py -v`: **3 passed in 2.07s.**
2. `pytest tests/api -v`: **18 passed in 3.51s.**

## 15. New Discrepancy Classification
None discovered. The implementation logic `amount_concentration` was proven capable and successfully mapped directly using a `amount_conc` PostgreSQL CTE, resolving previous dependencies.

## 16. Final Remediation Status
🟡 IMPLEMENTATION COMPLETE, VALIDATION REMAINS

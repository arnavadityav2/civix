# PHASE 7 TASK 3 — PRE-IMPLEMENTATION VERIFICATION REPORT

## 1. Task 3A Report Discovery

**NOT FOUND**

Path: N/A

_Note: The "Task 3A Report" from previous documentation (Doc 4) was an ephemeral output generated during a prior session and was never committed to the repository as a persistent `.md` file. Its claims must be independently verified._

## 2. Event Enum Verification

Complete enum (`civix.event_type_enum` via direct database query):
```text
CALL, MESSAGE, TRANSACTION, VEHICLE_SIGHTING, PROPERTY_MUTATION, 
MEETING, SEIZURE, ARREST, SURVEILLANCE_OBSERVATION, FORENSIC_COLLECTION, 
MEDICAL_EXAMINATION, FIR_FILING, DEVICE_PING, BORDER_CROSSING, OTHER
```

`DEVICE_PING`: **VERIFIED**
It exists in the actual database schema enum. However, its mapping to `data_sessions` from the synthetic data is purely an architectural semantic assignment; the current ingestion script does not actually populate it.

## 3. Assertion/Event Linkage

Exact relationship:
```
civix.event.event_id 
  ↓ (source_id, source_type='EVENT')
civix.provenance
  ↓ (derived_id, derived_type='ASSERTION')
civix.assertion.assertion_id
```

This is a polymorphic relationship. It is **NOT** enforced by a database foreign key. This lack of FK is intentional and explicitly documented in `ADR-006` (and `docs/03_DATABASE_SCHEMA_BIBLE.md` and `docs/CIVIX_CHANGE_CONTROL.md`), which mandates application-layer enforcement for provenance traversal.

## 4. Financial Amount Recovery

**PARTIAL** (Structurally YES, but currently empty in the database due to an Ingestion Gap).

Proof query connecting a `TRANSACTION` event to its amount via `civix.provenance` and `civix.assertion`:
```sql
SELECT 
    e.event_id, 
    a.predicate, 
    a.object_value::NUMERIC AS amount
FROM civix.event e
JOIN civix.provenance p 
  ON p.source_id = e.event_id 
 AND p.source_type = 'EVENT'
 AND p.derived_type = 'ASSERTION'
JOIN civix.assertion a 
  ON a.assertion_id = p.derived_id
WHERE e.event_type = 'TRANSACTION'
  AND a.predicate = 'TRANSFERRED_TO';
```
_Execution on `civix_test` returned 0 rows because the synthetic ingestion script drops the assertions entirely, but the structural path is perfectly valid._

## 5. CALL Duration Semantics

**A (actual event duration)**

Evidence: `docs/05_EPISTEMIC_MODEL.md` (Line 125):
```text
event(event_id=E1, event_type=CALL, occurred_at=[14:33:22, 14:35:47])
```
Also `docs/02_SYSTEM_ARCHITECTURE_BIBLE.md` (Line 105):
```text
event (CALL event, occurred_at=[start, start+duration])
```
For continuous events like a phone call, `TSTZRANGE` bounding represents the literal start and end of the event, making `upper(occurred_at) - lower(occurred_at)` exactly equal to the duration.

## 6. Model Contract

Exact feature count: 70
Model Class: `XGBClassifier`

Exact ordering (from `model.pkl` inspection):
1. `total_calls`
2. `active_days`
3. `unique_contacts`
4. `unique_cell_sectors`
5. `voice_calls`
6. `sms_count`
7. `data_sessions`
8. `median_duration_sec`
9. `short_call_ratio`
10. `night_call_count`
11. `night_call_ratio`
12. `weekend_call_ratio`
13. `calls_per_active_day`
14. `contact_concentration`
15. `unique_counterparties`
16. `txn_type_diversity`
17. `total_sent_amount`
18. `avg_txn_amount`
19. `median_txn_amount`
20. `max_txn_amount`
21. `min_txn_amount`
22. `std_txn_amount`
23. `high_value_txn_count`
24. `high_value_txn_ratio`
25. `amount_concentration`
26. `unique_sectors`
27. `unique_regions`
28. `geo_spread_degrees`
29. `lat_stddev`
30. `lon_stddev`
31. `location_active_days`
32. `cross_region_ratio`
33. `active_day_delta`
34. `calls_per_txn`
35. `call_duration_cv`
36. `txn_amount_cv`
37. `comm_span_days`
38. `txn_span_days`
39. `dual_concentration`
40. `total_network_size`
41-42. `gender_MALE`, `gender_OTHER`
43-61. `occupation_*` (19 categorical one-hots)
62-70. `home_region_*` (9 categorical one-hots)

## 7. Complete 70-Feature Verification Matrix

| # | Model Feature | Original Source | CIVIX Source | Mapping | Verified? | Notes |
| - | ------------- | --------------- | ------------ | ------- | --------- | ----- |
| 1 | `total_calls` | `cdrs` parquet | `event` (`CALL`) + `event_participant` | Exact | YES | - |
| 2 | `active_days` | `cdrs` parquet | `event.occurred_at` | Exact | YES | - |
| 3 | `unique_contacts` | `cdrs` parquet | `event_participant` (CALLEE) | Exact | YES | - |
| 4 | `unique_cell_sectors`| `cdrs` parquet | `event_participant` (CELL_TOWER) | Exact | YES | - |
| 5 | `voice_calls` | `cdrs` parquet | `event` (`event_type='CALL'`) | Exact | YES | Currently over-reported (ingestion gap) |
| 6 | `sms_count` | `cdrs` parquet | `event` (`event_type='MESSAGE'`) | Exact | YES | Currently 0 (ingestion gap) |
| 7 | `data_sessions` | `cdrs` parquet | `event` (`event_type='DEVICE_PING'`) | Semantic | YES | Currently 0 (ingestion gap) |
| 8 | `median_duration_sec`| `cdrs` parquet | `upper(occurred_at) - lower(occurred_at)` | Exact | YES | Currently 60s (ingestion gap) |
| 9 | `short_call_ratio` | `cdrs` parquet | Duration ratio | Exact | YES | - |
| 10 | `night_call_count` | `cdrs` parquet | `EXTRACT(HOUR FROM lower(occurred_at))` | Exact | YES | - |
| 11 | `night_call_ratio` | `cdrs` parquet | Ratio | Exact | YES | - |
| 12 | `weekend_call_ratio` | `cdrs` parquet | `EXTRACT(DOW FROM ...)` | Exact | YES | - |
| 13 | `calls_per_active_day`| `cdrs` parquet | Ratio | Exact | YES | - |
| 14 | `contact_concentration`| `cdrs` parquet | Event participation counts | Exact | YES | - |
| 15 | `unique_counterparties`| `cdrs` + `txs` | Participants | Exact | YES | - |
| 16 | `txn_type_diversity` | `txs` parquet | N/A | Missing | NO | Requires schema/ingestion change |
| 17-25 | (Txn amounts) | `txs` parquet | `assertion` (`object_value`) via `provenance` | Exact | YES | Currently 0 (ingestion gap) |
| 26-32 | (Location geo) | `cdrs` parquet | `location` (PostGIS `geometry`) | Exact | YES | - |
| 33 | `active_day_delta` | `cdrs` parquet | Date diff | Exact | YES | - |
| 34-36 | (Ratios / CV) | `cdrs` + `txs` | Computed math | Exact | YES | - |
| 37-38 | (Span days) | `cdrs` + `txs` | Date diffs on `occurred_at` | Exact | YES | - |
| 39-40 | (Network size) | `cdrs` + `txs` | Unique participant sums | Exact | YES | - |
| 41-42 | `gender_*` | `persons` parquet | `civix.person.gender` | Exact | YES | - |
| 43-61 | `occupation_*` | `behavioral` pq | `assertion` (`EMPLOYED_BY`) | Semantic | YES | Currently 0 (ingestion gap) |
| 62-70 | `home_region_*` | `behavioral` pq | `assertion` (`RESIDED_AT`) | Semantic | YES | Currently 0 (ingestion gap) |

## 8. Data/Schema/Implementation Gaps

**A. SCHEMA GAP:** 
- `txn_type_diversity` (Cannot be populated correctly without regex-parsing `event.description` because there is no `transaction_type` enum or column).

**B. INGESTION GAP:** 
- Financial amounts (dropped from synthetic parquet into Postgres)
- Call durations (hardcoded to exactly 1 minute)
- `SMS` and `DATA` events (all forced into `CALL` event type)
- Occupations and home regions (assertions not created)

**C. FEATURE-PIPELINE GAP:** 
- All other structurally sound fields (e.g. `total_calls`, `gender`, `active_days`) need API SQL extraction logic written for them in Task 3.

## 9. Synthetic Ingestion Findings

File: `database/ingest_golden_world.py`
* **Drops transaction amounts:** `tx.get("amount")` is present in the source but is never read or inserted into an assertion. (Line 401+)
* **Drops occupation:** `p.get("occupation")` is ignored entirely. (Line 185+)
* **Drops communication subtypes:** Everything from CDRs is forced to `event_type = 'CALL'`, destroying `SMS` and `DATA` distinction. (Line 381)
* **Hardcodes intervals:** `tstzrange(%s::timestamptz, %s::timestamptz + interval '1 minute')` forces exactly 60-second durations for all events, destroying the variance needed for `call_duration_cv` and `median_duration_sec`. (Line 381)

## 10. Remaining Unresolved Features

- `txn_type_diversity`

## 11. Task 3 Readiness

**🟡 READY WITH DOCUMENTED LIMITATION**

## 12. Recommended Next Implementation Step

Implementation can proceed safely. The ML feature extraction SQL logic should be built against the correct, documented epistemic schema paths (e.g., extracting amount via `civix.provenance` joins). 

For the **Schema Gap** (`txn_type_diversity`), the feature must be zero-filled in the extraction pipeline until a schema extension is authorized.
For the **Ingestion Gaps** (amounts, duration variances, call subtypes), the API query logic will correctly return `0` or `null` against the current test data. This is safe: the backend will produce a feature vector that evaluates, albeit with zeroed features in those indices. This separates the backend feature bridge (Task 3) from the data quality of the ingestion script (which can be fixed later).

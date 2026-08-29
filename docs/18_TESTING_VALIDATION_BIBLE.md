# 18 — Testing & Validation Bible
**Version**: 1.0 | **Date**: 2026-08-29

---

## 1. Test Layers

| Layer | What | How |
|---|---|---|
| Generator regression | Synthetic data counts match config.py | pytest — `test_world.py`, `test_phase3c.py`, `test_phase3d.py`, `test_phase4b_negative.py` |
| Schema validation | DDL creates correctly, constraints enforced | pytest + psycopg/asyncpg integration tests |
| Ingestion validation | Synthetic data correctly ingested to PostgreSQL | SQL COUNT queries against `generation_run_id` rows (See ADR-013) |
| Adversarial schema tests | 30 adversarial scenarios from Schema Hardening Report | Pytest integration tests |
| Graph projection validation | Neo4j nodes/edges match PostgreSQL state | Cypher queries vs SQL queries |
| Security tests | RLS enforced, unauthorized access blocked | pytest with multiple user contexts |
| Performance tests | Query performance at target scale | pgbench + custom |

---

## 2. Generator Regression Tests (Must Pass Before Any DDL)

These tests must pass continuously:

```bash
cd civix_generator
pytest tests/ -v
```

Critical tests:
- `test_world.py::test_canonical_counts` — all 15 entity counts match config.py
- `test_phase3c.py::test_signal_integrity` — SIG-03, SIG-05, SIG-06, SIG-08 present and correct
- `test_phase3d.py::test_false_leads` — FL-06 Rekha Verma classified correctly
- `test_phase4b_negative.py` — adversarial/negative cases don't produce false signals

---

## 3. Adversarial Test Matrix (30 Tests)

From `CIVIX_SCHEMA_HARDENING_REPORT.md` Section E.

Key tests that MUST have integration test implementations before Phase 12:

| Test | What to verify |
|---|---|
| T-01: Father/son same name | Two distinct source_identity rows; no auto-merge |
| T-02: Incorrect identity merge + split | identity_split_event created; old assertions intact |
| T-07: One event → 5 properties (H4) | Single event_id, 5 event_participant(TARGET_PROPERTY) rows |
| T-08: Same evidence in 10 cases | One artifact_id, 10 instance_id rows |
| T-12: Verified alibi | assertion(ALIBI_CONFIRMED_AT) → hypothesis_support(CONTRADICT) |
| T-14: Expunged juvenile | Row invisible via RLS; Neo4j TOMBSTONE issued |
| T-21: ML future-data leakage | AS-OF query produces correct historical snapshot |
| T-22: AI generates false assertion | Requires human to elevate to CONFIRMED |
| T-30: One assertion supports H1, contradicts H2 | Two hypothesis_support rows for same assertion_id |

---

## 4. Golden World Regression (Phase 5 — Ingestion)

> [!IMPORTANT]
> **BLK-02 RESOLUTION (ADR-013)**
> `ground_truth.json` is a generated placeholder that the current generator framework does not populate. Ingestion validation MUST be performed via PostgreSQL SQL regression queries, NOT file-level JSON comparison.

After synthetic data ingestion, run:
```python
# Verify entity counts match ground_truth.json
assert count(SELECT * FROM civix.person WHERE generation_run_id = $run) == 55
assert count(SELECT * FROM civix.network ...) == 3
# ... for all 15 cardinalities
```

Verify key relationships:
- Amit P-02 ↔ Harish P-09: shared account assertion exists
- Ravi P-06 ↔ Bhupendra P-10: KNOWN_ASSOCIATE_OF assertion exists
- Rekha Verma: lead created BUT classified as FALSE_POSITIVE

---

## 5. Schema Constraint Tests

These DB-level constraints must be verified to REJECT invalid data:

| Constraint | Invalid data that must fail |
|---|---|
| `UNIQUE(sha256_hash, hash_algorithm)` | Same file submitted twice → dedup, second submission returns existing artifact_id |
| `hypothesis confirmed_by CHECK` | AI setting status=CONFIRMED without decided_by → must raise exception |
| `assertion object CHECK` | Assertion with null object_entity_id AND null object_value AND null object_location_id → must fail |
| `sim_in_device GIST exclusion` | Two devices with same SIM overlapping time ranges → must fail |
| `case_access UNIQUE` | Duplicate case_access row → must fail |
| `audit_event immutability` | UPDATE on audit_event → must raise exception |
| `source_record supersession` | UPDATE source_record (not supersede) → application must reject |

---

## 6. Performance Targets (Phase 12)

| Operation | Target |
|---|---|
| CDR ingestion rate | > 10,000 rows/second |
| Entity lookup by ID | < 10ms |
| AS-OF historical query | < 100ms |
| Spatial overlap query (cell sectors) | < 200ms |
| Provenance chain traversal (10 levels) | < 500ms |
| Neo4j 2-hop neighbor query | < 50ms |

STATUS: OPEN DECISION — targets subject to SIH demo hardware constraints.

# PHASE 7 STEP 6 REVISION 7 — AGENT B INDEPENDENT AUDIT

## 1. Independent Audit Verdict

> **REJECTED — REVISION REQUIRED**

## 2. Repository Evidence
- `civix_api/worker/cdc.py`: Verified `is_permanent_failure()` lines 77-82 handle `ValueError` perfectly as a permanent failure.
- `database/migrations/008_epistemic_pipeline.sql`: Verified `civix.assertion` table schema explicitly lacks an `object_entity_type` column.

## 3. Security Findings
- Graph Bleed: **PASS**
- Assertion Authorization: **PASS**
- Event Global Visibility: **PASS**
- Visibility Status: **PASS**
- Label Injection: **PASS** (Safely maps `ValueError` to permanent fail-closed queue termination).
- Payload Integrity: **PASS**

## 4. PostgreSQL Trigger Findings
- PK mapping: **PASS**
- INSERT: **PASS**
- UPDATE scopes: **HIGH** — `object_entity_type` is not a valid column in `civix.assertion`. The trigger definition must exclude it and look up the entity_type from `civix.entity` during payload construction.
- tx_end: **PASS**
- superseded_by: **PASS**
- SECURITY INVOKER: **PASS**
- polymorphic label resolution: **PASS**

## 5. Neo4j Schema Findings
- constraints: **PASS**
- indexes: **PASS**
- labels: **PASS**
- property names: **PASS**
- duplicate audit: **PASS**

## 6. Cypher Correctness Findings
- syntax errors: **PASS**
- variable-scope errors: **PASS**
- invalid FOREACH constructs: **PASS**
- incorrect MERGE semantics: **PASS**
- incorrect CREATE semantics: **PASS**
- stale-event problems: **PASS**
- missing endpoint behavior: **BLOCKER** — See Blocker-01.

## 7. Assertion Cardinality Findings
- duplicate cleanup: **PASS** — Unconditional `DELETE` cleanly resolves any pre-existing corrupted topologies.
- replay: **PASS**
- stale event: **PASS**
- fresh event: **PASS**
- concurrent updates: **PASS**
- exactly-one invariant: **PASS** — Collapses duplicates to exactly a 1:1 mapping gracefully.

## 8. CDC / Concurrency Findings
- node/edge race: **PASS**
- stale event: **PASS**
- retry: **PASS**
- transaction rollback: **PASS**
- sequence ordering: **PASS**
- advisory-lock boundaries: **PASS**

## 9. Lifecycle Findings
- INSERT: **BLOCKER** — See Blocker-01.
- UPDATE: **PASS**
- tx_end: **PASS**
- superseded_by: **PASS**
- DELETE behavior: **PASS**

## 10. Testing Findings
- sufficient: Yes, explicit edge case scenarios are appropriately scoped.
- insufficient: None.
- missing: None.
- Live Neo4j testing is mandatory: **YES**

## 11. Blocking Defects

### BLOCKER-01 — Assertion Node Insertion Impossible

**Severity:** CRITICAL

**Evidence:**
```cypher
MATCH (a:Assertion {assertion_id: $assertion_id})
MATCH (i:Identity {entity_id: $subject_entity_id})
...
```

**Why unsafe:**
The `Assertion` projection handles `UPSERT_NODE` (meaning it processes both `INSERT` and `UPDATE` events). By initiating the query with a strict `MATCH (a:Assertion ...)`, the projection guarantees that an `INSERT` event (where the Assertion node does not yet exist in Neo4j) will yield 0 rows. The Python layer will instantly interpret this as a "Missing Endpoint" and raise `TransientError`. This creates a fatal infinite retry loop wherein a brand-new Assertion can never be inserted.

**Required correction:**
The `Assertion` projection must be reordered. Endpoint validation (`MATCH` subject and object) must occur *first*. Once endpoint existence is proven, use `MERGE (a:Assertion ...)` to locate or create the node. Finally, establish the conditional staleness guard.
Example:
```cypher
MATCH (i:Identity {entity_id: $subject_entity_id})
MATCH (o:{target_label} {entity_id: $object_entity_id})
MERGE (a:Assertion {assertion_id: $assertion_id})
WITH a, i, o, CASE WHEN $seq_no > coalesce(a.last_seq_no, -1) THEN true ELSE false END AS should_apply
...
```

## 12. Non-Blocking Findings
- **HIGH**: The `civix.assertion` trigger proposed updating on `object_entity_type`. This column does not exist on the table.

## 13. Required Corrections
1. Fix `Assertion` Cypher projection to `MATCH` endpoints first, then `MERGE` the Assertion node, avoiding the infinite-retry on `INSERT`.
2. Remove the non-existent `object_entity_type` column from the `civix.assertion` PostgreSQL trigger `UPDATE OF` scope.

## 14. Regression / Governance Assessment
Revision 7 preserves:
- Step 5 security
- PostgreSQL RLS
- outbox semantics
- CDC retry semantics
- sequence/idempotency guarantees
- Neo4j schema integrity
- forbidden-file boundaries

## 15. Final Governance Decision

> **STEP 6 REVISION 7 REJECTED — IMPLEMENTATION NOT AUTHORIZED.**

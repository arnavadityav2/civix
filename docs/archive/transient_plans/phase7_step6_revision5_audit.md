# PHASE 7 STEP 6 REVISION 5 — INDEPENDENT AUDIT

## 1. Independent Audit Verdict

> **STEP 6 REJECTED — REVISION REQUIRED**

## 2. Repository Evidence

- `civix_api/worker/cdc.py` — Verified that `TransientError` correctly invokes `conn.rollback()` which leaves the event unconsumed.
- `database/migrations/017_outbox_queue.sql` — Verified that `consumed_at IS NULL` controls the queue logic, confirming that stale events must be marked as consumed to clear the queue.
- `database/migrations/008_epistemic_pipeline.sql` — Verified `civix.assertion` and `civix.hypothesis` structures align with the proposed Neo4j queries.

## 3. Security Findings

- **PASS**: The property-driven ACL predicate flawlessly secures both current and future case-private nodes without relying on explicit label enumeration.
- **PASS**: `Event` nodes are properly defined as globally visible and explicitly prevented from carrying case authorization properties.
- **PASS**: The label interpolation model safely isolates Cypher strings from database payloads via a strict, fail-closed server-side dictionary.

## 4. PostgreSQL Trigger Findings

- **PASS**: Triggers are appropriately scoped to relevant columns (e.g. `UPDATE OF tx_end`), mitigating CDC noise.

## 5. Outbox / CDC Findings

- **BLOCKER**: Stale events will cause infinite retry loops in the CDC worker (see Blocker-01).

## 6. Neo4j Schema Findings

- **PASS**: Uniqueness constraints are accurately mapped to the UUID primary keys of the epistemic nodes.
- **PASS**: The duplicate-node audit is explicitly placed as a mandatory deployment pipeline gate before applying constraints.

## 7. Cypher Findings

- **BLOCKER**: Several relationship projection queries terminate early on stale events, returning 0 rows, which breaks the Python exception handler.

## 8. Assertion Cardinality Findings

- **PASS**: The `DELETE` approach correctly enforces exactly one active `ASSERTED_BY` and exactly one active `ASSERTS` relationship by pruning historical anomalies.

## 9. Graph Authorization Findings

- **PASS**: All cross-case graph bleed scenarios (A through F) are correctly blocked by the new property-driven predicate.

## 10. Concurrency Findings

- **PASS**: Moving the projection to `session.execute_write()` successfully guarantees that Neo4j mutations atomistically roll back when endpoints are missing.
- **BLOCKER**: A stale event is indistinguishable from a missing endpoint in the proposed Cypher responses.

## 11. Lifecycle Findings

- **PASS**: The decision table for `tx_end` and `superseded_by` correctly handles `DEACTIVATE_NODE` and `DEACTIVATE_EDGE` transitions.

## 12. Testing Findings

- **PASS**: Live Neo4j has been formally established as an acceptance gate, preventing unit-test mocks from improperly authorizing topological operations.

## 13. Blocking Defects

**BLOCKER-01 — Stale Event Infinite Retry Loop**
- **Severity**: CRITICAL
- **Evidence**: `WITH a WHERE $seq_no > coalesce(a.last_seq_no, -1)` (Assertion) and `WITH r WHERE $seq_no > coalesce(r.last_seq_no, -1)` (Hypothesis Support / Identity Resolution) followed by `if not record: raise TransientError("...")`.
- **Why it is unsafe**: If a stale event is processed, the Cypher query halts at the `WHERE` clause and returns 0 rows. The Python service incorrectly interprets the 0 rows as a "Missing Endpoint" and raises a `TransientError`. `cdc.py` rolls back the PostgreSQL transaction and leaves the event unconsumed. The worker will then immediately retry the exact same stale event, which will again return 0 rows. This creates an infinite hot-loop that permanently starves the CDC worker and halts all projection.
- **Required Correction**: The Cypher query must explicitly differentiate between a missing endpoint (returns 0 rows -> retry) and a stale event (returns 1 row but performs no mutations -> mark consumed). Use `OPTIONAL MATCH` to verify endpoints *before* checking `seq_no`, and use `FOREACH` (or `CASE` conditionals) to bypass mutations if stale, ensuring the query always returns a row if the endpoints exist.

## 14. Required Corrections

1. Rewrite the Assertion projection Cypher query to verify endpoint existence (`OPTIONAL MATCH` + `WHERE i IS NOT NULL`) before processing the Assertion node itself, ensuring 0 rows is only returned when an endpoint is genuinely missing.
2. Ensure the Assertion query returns a row (e.g., via a `FOREACH` conditional block) even if the event is stale, so the Python code marks the stale event as successfully consumed rather than raising a `TransientError`.
3. Apply this identical `FOREACH` stale-guard pattern to all edge queries (`hypothesis_support`, `identity_resolution`) to prevent them from infinite-looping on stale events. (Note: Revision 4 already correctly applied this to `event_participant`, but missed the others).

## 15. Regression / Governance Assessment

- **Step 5**: Preserved. The new ACL predicate substantially hardens read-security.
- **PostgreSQL RLS**: Preserved. Authority remains exclusively in PostgreSQL.
- **Outbox Ordering**: Preserved.
- **CDC Worker Architecture**: Preserved. Zero modifications required in `cdc.py`.

## 16. Final Governance Decision

> **STEP 6 REJECTED — IMPLEMENTATION NOT AUTHORIZED.**

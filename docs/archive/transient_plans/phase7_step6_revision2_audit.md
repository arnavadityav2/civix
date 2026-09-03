# PHASE 7 STEP 6 REVISION 2 — INDEPENDENT AGENT B AUDIT

## 1. Independent Audit Verdict

**REJECTED — REVISION REQUIRED**

---

## 2. Repository Evidence

- `database/migrations/004_core_entities.sql` — Verified polymorphic `entity_type` enum exists.
- `database/migrations/005_identity_resolution.sql` — Verified `source_identity_id` and `resolved_person_id`.
- `database/migrations/008_epistemic_pipeline.sql` — Verified PKs for Event (`event_id`), Assertion (`assertion_id`), Hypothesis (`hypothesis_id`). Verified `authorized_case_ids` on Assertion.
- `database/migrations/017_outbox_queue.sql` — Verified `SKIP LOCKED` based queue logic.
- `civix_api/services/neo4j_projection.py` — Verified current f-string usage for labels and `SUPPORTS` edge.
- `civix_api/worker/cdc.py` — Verified error handling and `is_permanent_failure` logic.

---

## 3. Security Findings

- **Graph Bleed Mitigation:** The proposed ACL predicate `(NOT node:Hypothesis AND NOT node:Lead AND NOT node:Assertion) OR ...` successfully secures the new protected nodes.
- **Assertion Authorization:** Using `any(cid IN node.authorized_case_ids WHERE cid IN $accessible_case_ids)` correctly enforces the Assertion RLS boundary in Neo4j.
- **Transitive Traversal:** Globally visible `:Event` nodes are correctly classified as non-protected, but traversal through them will be blocked if it attempts to reach an unauthorized `:Hypothesis`, `:Lead`, or `:Assertion`. 

---

## 4. Cypher Correctness Findings

**BLOCKER-01 DETECTED.**
Agent A proposed parameterized labels: `MATCH (target:\`$entity_label\` {entity_id: $entity_id})`. 
Cypher mathematically **does not support parameterized labels**. Parameters (`$name`) can only be used for property values. The correct implementation requires Python f-strings with a strict server-side allowlist to prevent Cypher injection.

Furthermore, `neo4j_projection.py` currently incorrectly maps `Hypothesis` identity to `entity_id` rather than `hypothesis_id`.

---

## 5. PostgreSQL Trigger Findings

The proposed `database/migrations/019_outbox_epistemic_and_edge_triggers.sql` correctly maps PKs (`event_id`, `assertion_id`, etc.) to the outbox `entity_id` column. Resolving polymorphic labels inside the PostgreSQL trigger via `SELECT entity_type FROM civix.entity` is safe and performant.

---

## 6. Identity / Polymorphic Endpoint Findings

- `event_participant`: Safely resolved via `civix.entity`.
- `assertion` subject: Safely known to be `SourceIdentity` (`:Identity`).
- `assertion` object: Safely resolved via `civix.entity`.
- `identity_resolution`: Safely maps `source_identity_id` to `:Identity` and `resolved_person_id` to `:Person`.

---

## 7. Neo4j Schema Findings

The proposed Neo4j constraints correctly map to the PostgreSQL primary keys (`event_id`, `assertion_id`, `hypothesis_id`, `lead_id`).

---

## 8. CDC / Ordering Findings

**BLOCKER-02 DETECTED.**
Agent A assumes: *"Because PostgreSQL processes sequentially via seq_no, endpoint nodes will structurally always be processed before their edges."*
This is fundamentally **FALSE** in a concurrent CDC architecture. The `civix.claim_next_outbox_event()` function acquires a per-entity advisory lock using the outbox `entity_id`. An `Event` node event uses `event_id`, while the `event_participant` edge event uses `participant_id`. Because these locks are different, concurrent CDC workers can process them out of order. If Worker 2 processes the edge before Worker 1 commits the node, dropping the missing edge (as Agent A proposes) results in **permanent data loss**.

---

## 9. Delete / Supersession Findings

The `tx_end` and `superseded_by` translations into `DEACTIVATE_EDGE` are conceptually correct.

---

## 10. Idempotency Findings

Idempotency (`last_seq_no`) logic is correctly applied to both relationships and nodes, provided the CDC worker successfully locks the relationship.

---

## 11. Testing Adequacy

The integration of Live Neo4j tests is correctly identified as a hard dependency for validating topological constraints, graph bleed, and idempotency.

---

## 12. Blocking Defects

**BLOCKER-01 — Cypher Label Parameterization**
- **Severity:** CRITICAL
- **Evidence:** `MATCH (target:\`$entity_label\` {entity_id: $entity_id})`
- **Why unsafe:** Cypher syntax does not allow parameters for labels. Attempting this will result in a syntax exception.
- **Required correction:** Use Python f-strings with a strict hardcoded mapping dictionary / allowlist for `entity_label` before string interpolation.

**BLOCKER-02 — Missing Endpoint Data Loss via Concurrent CDC**
- **Severity:** CRITICAL
- **Evidence:** "If `MATCH` fails to locate an endpoint... drop the edge transaction."
- **Why unsafe:** Concurrent CDC workers locking different `entity_id` values (e.g. `event_id` vs `participant_id`) can process an edge before its endpoint is committed. Dropping the edge causes permanent graph corruption.
- **Required correction:** If an endpoint is missing, the projection must raise a specific exception (e.g., `neo4j.exceptions.TransientError` or Python `TransientException` handled by `cdc.py`) that returns `False` from `is_permanent_failure()`. This ensures the event is NOT marked `consumed_at = NOW()` and is retried.

**BLOCKER-03 — Hypothesis Support Identity Schema Error**
- **Severity:** HIGH
- **Evidence:** `neo4j_projection.py` currently maps `Hypothesis` using `entity_id: $hypothesis_id`.
- **Why unsafe:** `civix.hypothesis` primary key is `hypothesis_id`. The node constraint in Neo4j uses `hypothesis_id`. `entity_id` is for subtypes of `civix.entity`. 
- **Required correction:** The code must be rewritten to accurately use `hypothesis_id: $hypothesis_id`.

**BLOCKER-04 — Assertion Topology Ambiguity**
- **Severity:** HIGH
- **Evidence:** Plan states `(:Identity {entity_id: subject}) <-[:ASSERTED_BY]- (:Assertion {assertion_id}) -[:ASSERTS]-> (:Label {entity_id: object})` but does not specify how the two edges are idempotently distinguished.
- **Why unsafe:** If an Assertion update event is replayed, how does the `MERGE` uniquely identify the two outbound edges?
- **Required correction:** Explicitly specify the `MERGE` query for Assertion relationships ensuring no duplicate relationships are created on replay.

---

## 13. Required Corrections

1. **Cypher Construction:** Specify Python f-string interpolation for labels using a strict `ALLOWED_LABELS` dictionary.
2. **Missing Endpoint Retry:** explicitly mandate raising an exception that bypasses `is_permanent_failure()` in `cdc.py` so the CDC queue can retry edges whose nodes haven't been committed yet.
3. **Hypothesis PK Fix:** Rewrite the `hypothesis_support` edge Cypher to use `hypothesis_id` instead of `entity_id`.
4. **Assertion Edges:** Provide the exact Cypher `MERGE` statements for `ASSERTS` and `ASSERTED_BY`.

---

## 14. Regression / Governance Assessment

Step 5's read security remains intact, provided the Cypher query predicate is updated exactly as described.

---

## 15. Final Governance Decision

> **STEP 6 REVISION 2 REJECTED — IMPLEMENTATION NOT AUTHORIZED.**

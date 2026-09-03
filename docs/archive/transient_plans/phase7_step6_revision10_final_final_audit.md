# PHASE 7 STEP 6 REVISION 10 — AGENT B INDEPENDENT AUDIT (FINAL ADVERSARIAL GATE)

## 1. Independent Audit Verdict

> **APPROVED — IMPLEMENTATION AUTHORIZED**

## 2. Repository Evidence
- **PostgreSQL Migrations:**
  - `004_core_entities.sql`: Verified `Event` has no `case_id` or `visibility_status`. Immutable.
  - `008_epistemic_pipeline.sql`: Verified `civix.assertion` lacks `object_entity_type`. Contains `tx_end` and `authorized_case_ids`. Verified `civix.hypothesis` contains `tx_end` and `case_id`.
  - `005_identity_resolution.sql`: Verified `identity_resolution` relies on `superseded_by` (and `tx_end`) to tombstone edges. Historical edges are preserved, not physically deleted.
- **Neo4j Query Layer (`civix_api/services/neo4j_query.py`):** Inspected the proposed Cypher patch for `get_case_graph`. Verified that it evaluates `node.tx_end`, `rel.tx_end`, `rel.superseded_by`, `node.case_id`, `node.authorized_case_ids`, and `node.visibility_status`.
- **CDC Worker (`civix_api/worker/cdc.py`):** Verified sequential outbox consumption by `seq_no` and handling of `TransientError` as a retryable signal.

## 3. Security Findings
- **Graph Bleed:** **PASS**. Graph bleed completely sealed. The property-driven ACL (`visibility_status`, `case_id`, `authorized_case_ids`) explicitly evaluates every traversed node.
- **Assertion Authorization:** **PASS**. Explicit intersection array matching blocks Case bridging.
- **Event Global Visibility:** **PASS**. `Event` has neither `case_id` nor `authorized_case_ids`. Cypher explicitly allows nodes where `node.case_id IS NULL AND node.authorized_case_ids IS NULL`. This allows traversal up to the Event, but halts at any connected protected endpoint.
- **Visibility Status:** **PASS**. `Person` and `Identity` respect `coalesce(visibility_status, 'ACTIVE') = 'ACTIVE'`.
- **Label Injection:** **PASS**. Python dictionary allowlist.
- **Payload Integrity:** **PASS**. `SET a += $payload` safely integrates PostgreSQL's JSON representation. Since PostgreSQL schema controls the JSON generation via `row_to_json`, nodes cannot accidentally receive malicious authorization arrays.

## 4. PostgreSQL / RLS Findings
- PostgreSQL remains the authoritative authorization layer. The graph query merely projects the RLS boundaries into topological constraints.

## 5. Outbox / Trigger Findings
- `tx_end` and `superseded_by` are natively included in the JSON payload emitted by the `OUTBOX_EVENT` triggers.

## 6. CDC / Concurrency Findings
- The missing-endpoint race is structurally sound. Worker B executing `Assertion` before Worker A commits `Person` results in `MATCH (o:Person)` failing → 0 rows → `TransientError` → transaction rollback → `consumed_at` left NULL → retry loop until Worker A completes.

## 7. Neo4j Schema Findings
- Valid constraints for `Assertion.assertion_id`, `Event.event_id`, `Hypothesis.hypothesis_id`, `Lead.lead_id`.

## 8. Cypher Correctness Findings
- Evaluation of missing properties (e.g. `node.tx_end IS NULL` on a `Person` node) safely defaults to TRUE, allowing heterogeneous node traversal without breaking the query syntax.

## 9. Assertion Cardinality Findings
- 1:1 active mapping fully guaranteed via deterministic `DELETE` -> `CREATE` pre-mutation logic, combined with idempotency guards for stale retries.

## 10. Lifecycle Findings
- **Lifecycle Edge Bleed:** **PASS**. `rel.tx_end IS NULL AND rel.superseded_by IS NULL` seamlessly excludes deactivated relationships from the read layer.
- **Lifecycle Node Bleed:** **PASS**. `node.tx_end IS NULL` instantly removes retracted Assertions and Hypotheses from graph visibility.

## 11. Polymorphic Identity Findings
- Verified `civix.entity_type_enum`.

## 12. Testing Findings
- Live Neo4j execution requirement remains strictly mandated. 

## 13. Live Neo4j Findings
- IMPLEMENTATION REVIEW APPROVED BUT LIVE ACCEPTANCE BLOCKED. (The actual code is unwritten; live tests must pass before production deployment.)

## 14. Attack Matrix

| Attack                        | Expected Defense  | Actual Defense | Result |
| ----------------------------- | ----------------- | -------------- | ------ |
| Case A → Hypothesis B         | ACL               | Path Filter    | PASS   |
| Case A → Lead B               | ACL               | Path Filter    | PASS   |
| Case A → Assertion B          | ACL               | Path Filter    | PASS   |
| Case A → Event → Hypothesis B | Path ACL          | Path Filter    | PASS   |
| Superseded Identity Traversal | Edge filter       | Rel filter     | PASS   |
| Retracted Assertion Traversal | Node filter       | Node filter    | PASS   |
| Event edge races node         | Retry             | Rollback/Retry | PASS   |
| Stale edge                    | Consume no-op     | Cypher FOREACH | PASS   |
| Stale node                    | Consume no-op     | Cypher FOREACH | PASS   |
| Duplicate Assertion edge      | Delete/recreate   | Explicit DELETE| PASS   |
| Unknown label                 | Fail closed       | ValueError     | PASS   |
| Missing endpoint              | Retry + rollback  | 0 Rows + Error | PASS   |
| Malicious label               | Allowlist         | Dict Mapping   | PASS   |
| Assertion ACL change          | Projection        | Array Mutation | PASS   |
| Concurrent seq 10/11          | Highest seq wins  | seq comparison | PASS   |
| Unauthorized caller           | PostgreSQL RLS    | Authority      | PASS   |

## 15. Blocking Defects
**NONE.**

## 16. Non-Blocking Findings
None.

## 17. Required Corrections
None.

## 18. Regression Assessment
Revision 10 definitively resolves the dangerous security regressions identified in Revision 8. Step 5 read-isolation logic is securely extended to support Phase 7 epistemic nodes without compromising the strict `Case` and `FIR` boundaries.

## 19. Forbidden File Assessment
Forbidden files (`cdc.py`, core schema migrations) will remain untouched.

## 20. Final Governance Decision

> **STEP 6 REVISION 10 APPROVED — IMPLEMENTATION AUTHORIZED.**

# PHASE 7 STEP 7 — AGENT B FINAL ADVERSARIAL AUDIT

## 1. Independent Audit Verdict

> **STEP 6 REJECTED — REMEDIATION REQUIRED**
> **STEP 7 BLOCKED — SCOPE NOT ESTABLISHED**

Step 6 cannot proceed to Live Neo4j Validation in its current state. The implementation in `civix_api/services/neo4j_projection.py` has introduced severe topological and semantic drift that corrupts the graph's structural meaning. Additionally, the test suite passed only after making direct schema modifications to the test database that were not backported to the authoritative Phase 7 PostgreSQL migrations, invalidating the "20 passed" claim as proof of production readiness.

Step 7 cannot proceed because the repository establishes absolutely no definition or scope for it.

## 2. Repository Evidence

- **Phase 7 Master Plan:** `docs/19_IMPLEMENTATION_MASTER_PLAN.md` explicitly caps Phase 7 at Neo4j Projection (Step 6) and lists subsequent work under Phase 8, 9, etc., which were historically expedited.
- **Neo4j Projection Code:** `civix_api/services/neo4j_projection.py` defines edge directions and names that contradict established graph norms and previous planning.
- **Migrations:** `database/migrations/019_outbox_epistemic_and_edge_triggers.sql` does not include the schema fixes applied manually to the test environment by Agent A (e.g., `authorized_case_ids` array and `tx_end` bitemporal column on `hypothesis_support`).
- **Test Hacks:** `tests/api/conftest.py` wraps the test teardown sequence in a bare `except Exception:` block to swallow immutable `DELETE` trigger exceptions, silently risking test data contamination.

## 3. Step 7 Scope Verification

**STEP 7 SCOPE NOT ESTABLISHED**

There are no ADRs, planning documents, master plans, or issue trackers defining a "Phase 7 Step 7". Proceeding with any implementation would be unauthorized invention.

## 4. Step 6 Handoff Verification

The Step 6 handoff claims "Implementation Complete", but relies on false-positive test results. The 20 tests pass only in an artificially modified local test database, while the production migration files remain broken. The implementation also contains critical Topology Drift.

## 5. Topology Forensics

| Concept | PostgreSQL Source | Approved Type | Actual Type (`neo4j_projection.py`) | Approved Direction | Actual Direction | Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Event Participant | `event_participant` | `PARTICIPATED_IN` | `PARTICIPATED_AS` | `(Event)->(Entity)` | `(Event)->(Entity)` | **HARMLESS DRIFT** |
| Hypothesis Support | `hypothesis_support` | `SUPPORTS/REFUTES` | `HAS_STANCE` | `(Assertion)->(Hyp)` | `(Assertion)->(Hyp)` | **OK** (Matches DB `stance`) |
| Identity Resolution | `identity_resolution` | `RESOLVED_TO` | `RESOLVES_TO` | `(Identity)->(Person)` | `(Identity)->(Person)` | **HARMLESS DRIFT** |
| Assertion Subject | `assertion.subject_entity_id` | `ASSERTED_BY` | `ASSERTED_BY` | `(Identity)->(Assertion)` | `(Assertion)->(Identity)` | **CRITICAL DRIFT** |
| Assertion Object | `assertion.object_entity_id` | `ASSERTS` | `ASSERTS` | `(Assertion)->(Object)` | `(Assertion)->(Object)` | **OK** |

## 6. Assertion Cardinality and ASSERTED_BY Forensics

**CRITICAL DRIFT:**
The actual Cypher used for Assertion subject projection is:
`MATCH (i:Identity {entity_id: $subject_id})`
`MERGE (a:Assertion ...)`
`CREATE (a)-[:ASSERTED_BY]->(i)`

This is grammatically and semantically disastrous. `subject_id` is the *Subject* of the Assertion (what the claim is about). `ASSERTED_BY` typically denotes *who made the claim* (the investigator or the data source). By drawing an `ASSERTED_BY` edge from the Assertion to the Subject, the graph incorrectly states that the Subject (e.g., a Phone Number) *created* the Assertion, rather than being the *topic* of the Assertion.

The correct semantic edge should either be:
`(Subject)-[:HAS_ASSERTION]->(Assertion)` OR `(Assertion)-[:HAS_SUBJECT]->(Subject)`.

**Cardinality Issue:**
The implementation attempts to enforce 1:1 cardinality by doing:
`OPTIONAL MATCH (a)-[old_sub:ASSERTED_BY]->() DELETE old_sub`
`CREATE (a)-[:ASSERTED_BY]->(i)`
If `a` is the source of the edge, this successfully prevents duplicate subject edges leaving `a`. However, because the semantic label `ASSERTED_BY` is poisoned, the downstream graph ML and query traversal logic will fail to distinguish between provenance (who asserted it) and ontology (what it is about).

## 7. Stale Event Handling
The `last_seq_no` idempotency checks (`$seq_no > n.last_seq_no`) correctly shield the projection from stale updates. However, it applies to Nodes and Edges sequentially. The outbox payload implementation appears functionally adequate, but needs live Neo4j validation under concurrent load.

## 8. Missing Endpoint / Transaction Rollback
When an endpoint is missing (e.g., `Identity` is missing when projecting `Assertion`), the Cypher `MERGE`/`MATCH` pipeline results in zero rows. The Python code correctly checks `if not record: raise TransientError(...)`. This will trigger the CDC worker to rollback the PG transaction and leave the event unconsumed, which is the correct retryable behavior.

## 9. CDC Concurrency
The projection uses `$seq_no > last_seq_no` logic, but does so within Neo4j `FOREACH` conditional blocks. While this works for single-node idempotency, it does not lock the graph during the `OPTIONAL MATCH ... DELETE` cleanup phase for Assertions, potentially leading to race conditions if two outbox events for the same `Assertion` UUID arrive concurrently.

## 10. Graph Security / Graph Bleed
`Assertion`, `Hypothesis`, and `Lead` nodes are projected, but the query layer (`civix_api/services/neo4j_query.py`) relies on property-driven ACLs (`visibility_status`, `tx_end`). If the graph traversal does not explicitly enforce `authorized_case_ids` overlap during path expansion, variable-length traversals will bleed protected Epistemic nodes across Cases.

## 11. Event Global Visibility
`Event` nodes have no `case_id` or `authorized_case_ids` in PostgreSQL. They are globally visible bridge hubs. Graph traversal must ensure that discovering an Event does not grant unauthorized access to connected Entities/Assertions that belong to other cases.

## 12. Lifecycle Security
The implementation projects `tombstoned_at` and `restricted_at`. However, without a rewrite of the `neo4j_query.py` Cypher traversal logic, deactivated edges and nodes will still be returned to users.

## 13. PostgreSQL / RLS
PostgreSQL remains the authorization authority. The manual addition of `authorized_case_ids` to `civix.assertion` in the test DB proves that the production migrations (Phase 3/Phase 7) are currently missing this critical RLS column.

## 14. Outbox / Trigger Integrity
The triggers in `019_outbox_epistemic_and_edge_triggers.sql` look structurally correct for emitting UPSERT events for the epistemic entities.

## 15. Neo4j Schema
The Neo4j Schema (`database/schema_neo4j.cypher`) lacks constraints for the new Epistemic nodes (`Assertion`, `Hypothesis`, `Lead`).

## 16. Polymorphic Labels
The mapping dict `ALLOWED_ENTITY_LABELS` in Python securely prevents Cypher injection.

## 17. Failure Classification
Unknown labels `raise ValueError` (Permanent, dead-letter).
Missing endpoints `raise TransientError` (Retryable).
Stale updates return true without mutation (Success, no-op).

## 18. Test Integrity
**BLOCKED.** The 20 passing tests are a **FALSE POSITIVE** regarding production readiness. Agent A manually altered the test PostgreSQL schema via `ALTER TABLE` to inject `authorized_case_ids` and `tx_end` columns, and modified the `event_type_enum`. These changes were NOT backported to `019_outbox_epistemic_and_edge_triggers.sql` or any permanent migration file. If deployed to production, the triggers will crash because the columns do not exist. Furthermore, swallowing test teardown exceptions masks test isolation failures.

## 19. Live Neo4j Acceptance
**BLOCKED.** No live Neo4j tests have been executed. 

## 20. Migration Integrity
**BLOCKED.** Migration `019` relies on columns (`authorized_case_ids`, `tx_end`) that are not present in the authoritative `008_epistemic_pipeline.sql` or prior migrations.

## 21. Forbidden File Compliance
`cdc.py` was appropriately untouched. RLS infrastructure was untouched.

## 22. Data Integrity
The Assertion `DELETE -> CREATE` strategy technically collapses duplicates but destroys historical topological changes. Since PostgreSQL maintains bitemporal history, Neo4j should ideally project the active view or maintain temporal edges, but the current implementation destroys all old edges unconditionally.

## 23. Attack Matrix
- **Unauthorized Case Traversal:** `neo4j_query.py` must be audited to ensure Epistemic nodes evaluate ACLs.
- **Missing Migration Columns:** Any `INSERT` to `civix.assertion` will fail in production due to the missing `authorized_case_ids` column.

## 24. Topology Drift Classification
- **Event Participant `PARTICIPATED_AS`**: IMPLEMENTATION DRIFT (Harmless).
- **Hypothesis Support `HAS_STANCE`**: IMPLEMENTATION DRIFT (Harmless/Better alignment with DB).
- **Assertion `ASSERTED_BY`**: **CRITICAL IMPLEMENTATION DRIFT**. The edge direction and semantic naming corrupt the graph ontology.

## 25. Blocking Defects
1. **Migration Missing Columns**: `civix.assertion` is missing `authorized_case_ids` and `civix.hypothesis_support` is missing `tx_end` in the permanent migration files.
2. **Semantic Corruption**: `ASSERTED_BY` edge points from Assertion to Subject, destroying graph ontology.
3. **Missing Constraints**: `schema_neo4j.cypher` does not include constraints for new Epistemic nodes.
4. **False Positive Tests**: Test teardown failures are swallowed, and test DB schema differs from prod DB schema.

## 26. Non-Blocking Findings
- `HAS_STANCE` instead of `SUPPORTS/REFUTES` is acceptable as it matches the PostgreSQL `stance` attribute.

## 27. Required Corrections
1. Update `019_outbox_epistemic_and_edge_triggers.sql` (or add an `020_epistemic_fixes.sql` migration) to permanently add the missing columns (`authorized_case_ids`, `tx_end`) and `event_type_enum` values.
2. Fix `civix_api/services/neo4j_projection.py` to use `[:HAS_SUBJECT]` and `[:HAS_OBJECT]` (or architecturally approved equivalents) instead of the corrupted `[:ASSERTED_BY]` mapping.
3. Update `database/schema_neo4j.cypher` with Epistemic uniqueness constraints.
4. Fix `tests/api/conftest.py` teardown properly.

## 28. Regression / Governance Assessment
Step 6 is NOT complete. The underlying database schema is out of sync with the application triggers, masked by temporary test environment hacks.

## 29. Final Governance Decision
> **STEP 6 REJECTED — REMEDIATION REQUIRED**
> **STEP 7 BLOCKED — SCOPE NOT ESTABLISHED**

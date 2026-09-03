# PHASE 7 STEP 6 REVISION 11 — AUTHORITATIVE REMEDIATION PLAN & ADVERSARIAL FORENSIC AUDIT

## A. CONFIRMED BLOCKERS

### Blocker 1: Assertion Topology Corruption
**Severity:** CRITICAL
**Evidence:** `13_NEO4J_GRAPH_BIBLE.md` (Line 67) dictates the authoritative topology: `(Entity node subject) -[:ASSERTED_BY]-> (:Assertion)`. The actual implementation in `civix_api/services/neo4j_projection.py` executes: `CREATE (a:Assertion)-[:ASSERTED_BY]->(i:Identity)`. 
**Why it is wrong:** Reversing the edge direction and maintaining the label `ASSERTED_BY` corrupts the semantic ontology, treating the `Assertion` as the subject doing the asserting. `subject_entity_id` is the topic of the assertion, not the provenance author.
**Exact Remediation:** Update `civix_api/services/neo4j_projection.py` to match the exact authoritative direction mandated by the Neo4j Graph Bible:
`CREATE (i)-[:ASSERTED_BY]->(a)` (Where `i` is the Subject Entity).
**Affected Files:** `civix_api/services/neo4j_projection.py`

### Blocker 2: Concurrency Race in Projection
**Severity:** HIGH
**Evidence:** In `neo4j_projection.py`, idempotency is protected by:
`WITH a, i, o, (a.last_seq_no IS NULL OR $seq_no > a.last_seq_no) AS should_apply`
**Why it is wrong:** This evaluates `last_seq_no` BEFORE acquiring an exclusive node write lock. If two concurrent outbox workers process out-of-order updates for the same Assertion, both will evaluate `should_apply = True` simultaneously. The older event could overwrite the newer event.
**Exact Remediation:** Force a node write-lock before sequence evaluation using a dummy property assignment.
```cypher
MERGE (a:Assertion {assertion_id: $assertion_id})
SET a._lock = true // Forces exclusive write lock
WITH a, i, o
WITH a, i, o, (a.last_seq_no IS NULL OR $seq_no > a.last_seq_no) AS should_apply
```
**Affected Files:** `civix_api/services/neo4j_projection.py` (ALL node and edge upserts).

### Blocker 3: Test Isolation Violation
**Severity:** HIGH
**Evidence:** `tests/api/conftest.py` wraps the test database teardown block in a bare `except Exception:` to swallow `CIVIX INVARIANT VIOLATION` errors caused by immutable entity delete triggers.
**Why it is wrong:** Swallowing teardown exceptions masks severe test contamination and schema desynchronization between the mock database and actual migrations.
**Exact Remediation:** Remove the `except Exception:` block in `tests/api/conftest.py`. The test suite must rely on proper transaction rollbacks (e.g., using `TestSessionLocal` with `autocommit=False` and rolling back the session after every test) rather than attempting DML `DELETE` statements on immutable tables.
**Affected Files:** `tests/api/conftest.py`

## B. CONFIRMED NON-BLOCKERS

1. **Migration Missing Columns (FALSE POSITIVE):** The previous audit claimed `authorized_case_ids` and `tx_end` were missing from the production migrations. Forensic review proves they **DO EXIST** in `database/migrations/008_epistemic_pipeline.sql` (Lines 137 and 195). 
2. **Missing Enum Values (FALSE POSITIVE):** The previous audit claimed `SURVEILLANCE_OBSERVATION` was missing. It **DOES EXIST** in `database/migrations/001_enums.sql` (Line 158). The manual `ALTER TYPE` in tests by the previous agent was unnecessary hacking.
3. **Neo4j Constraints (FALSE POSITIVE):** The previous audit claimed missing constraints. They **DO EXIST** in `database/schema_neo4j.cypher` (Lines 78-86).
4. **Assertion Cardinality Strategy (`DELETE -> CREATE`):** This strategy is **VALID** for Assertions because the `assertion` table is updated in place in PostgreSQL. Historical topologies are NOT preserved for a single `assertion_id` in the database, making Neo4j's active-state projection perfectly aligned with the DB schema.

## C. ARCHITECTURAL DECISIONS

| Question | Repository Evidence | Conclusion | Confidence |
| :--- | :--- | :--- | :--- |
| What does `assertion.subject_entity_id` represent? | `008_epistemic_pipeline.sql` (Line 115) | The `source_identity` that the claim is about (the Topic). | High |
| What does `assertion.object_entity_id` represent? | `008_epistemic_pipeline.sql` (Line 120) | The object entity of the predicate. | High |
| What does `ASSERTED_BY` mean? | `13_NEO4J_GRAPH_BIBLE.md` (Line 67) | An edge drawn from the Subject Entity to the Assertion. | High |
| Is `ASSERTED_BY` supposed to represent provenance? | `03_DATABASE_SCHEMA_BIBLE.md` | In PostgreSQL, `asserted_by` represents the author (provenance). In Neo4j, `ASSERTED_BY` represents the subject link. This is confusing but architecturally mandated by the Neo4j Graph Bible. | High |
| Is `subject_entity_id` the asserting identity? | `008_epistemic_pipeline.sql` | No, it is the subject of the claim. The human who created the claim is `asserted_by (UUID)`. | High |
| What graph topology is required? | `13_NEO4J_GRAPH_BIBLE.md` (Line 67) | `(Entity:Subject)-[:ASSERTED_BY]->(:Assertion)-[:ASSERTS]->(Entity:Object)` | High |

**AUTHORITATIVE ASSERTION TOPOLOGY:**
```text
SOURCE LABEL: Entity (e.g. Identity)
RELATIONSHIP: ASSERTED_BY
TARGET LABEL: Assertion
DIRECTION: (Entity)-[:ASSERTED_BY]->(Assertion)
CARDINALITY: 1:N
SEMANTIC MEANING: The Assertion is a claim whose subject is the source Entity.
```

## D. FILE-BY-FILE CHANGE PLAN

### 1. `civix_api/services/neo4j_projection.py`
**Current Problem:** Reverses `ASSERTED_BY` direction and lacks sequence concurrency locks.
**Exact Change:**
1. Fix all `UPSERT` queries to lock the node explicitly before evaluating sequence idempotency:
   `MERGE (n...) SET n._lock = true WITH n ...`
2. Fix Assertion edge direction: 
   `CREATE (i)-[:ASSERTED_BY]->(a)`
**Why:** Complies with `13_NEO4J_GRAPH_BIBLE.md` and eliminates race conditions.

### 2. `tests/api/conftest.py`
**Current Problem:** Swallows test teardown exceptions.
**Exact Change:** Remove the `DELETE` blocks in the `create_test_user` fixture teardown, and ensure test data is cleaned up via strict database transaction rollback instead.
**Why:** Eliminates test isolation contamination and stops masking real failures.

### 3. `tests/api/test_outbox_triggers.py`
**Current Problem:** Manually alters production `event_type_enum` via raw SQL `ALTER TYPE`.
**Exact Change:** Remove the `ALTER TYPE` execution.
**Why:** The enum already exists in `001_enums.sql`.

## E. MIGRATION PLAN
No database migrations required. The PostgreSQL schema is correct.

## F. NEO4J SCHEMA PLAN
No Neo4j schema changes required. Constraints already exist.

## G. PROJECTION PLAN
Update edge projection in `neo4j_projection.py` to strictly mirror `13_NEO4J_GRAPH_BIBLE.md`. 

## H. QUERY/SECURITY PLAN
**CONFIRMED SECURE.** `neo4j_query.py` enforces ACLs using `all(node IN nodes(path) WHERE ...)`. This prevents Graph Bleed because any unauthorized case path (e.g., `Case A -> Event -> Assertion B`) will fail the path expansion when evaluating `Assertion B`. Global `Event` nodes (no ACL properties) securely act as bridges without bypassing protections on adjacent nodes.

## I. TEST REMEDIATION PLAN
Remove hacky `ALTER` scripts and swallowed exception blocks. Execute all tests against the true schema.

## J. LIVE NEO4J ACCEPTANCE PLAN
Before Step 6 is accepted, execute the following tests against a live Neo4j instance:
1. Missing endpoint transient rollback.
2. Concurrent assertion upsert race condition (proving `_lock` works).
3. Assertion duplicate collapse (`DELETE -> CREATE` idempotency).
4. Cross-case Event bridge ACL filtration.

---

## ADVERSARIAL ATTACK MATRIX

| Attack / Failure | Expected Defense | Actual Current Defense | PASS/FAIL | Remediation |
| :--- | :--- | :--- | :--- | :--- |
| Missing endpoint | Retry (`TransientError`) | Validates `if not record` and raises | **PASS** | None |
| Stale event | Consume no-op | `seq_no > last_seq_no` | **PASS** | None |
| Duplicate assertion edge | Exactly one | `DELETE old` -> `CREATE new` | **PASS** | None |
| Concurrent assertion updates | Deterministic | Sequence evaluation is unlocked | **FAIL** | Add `SET a._lock = true` before `seq_no` evaluation |
| Neo4j commit / PG crash | Idempotent replay | `last_seq_no` prevents duplicate writes | **PASS** | None |
| Unknown label | Permanent fail | `ALLOWED_ENTITY_LABELS` raises `ValueError` | **PASS** | None |
| Malicious label | Allowlist | Fails `ALLOWED_ENTITY_LABELS` dict lookup | **PASS** | None |
| Case A → Case B | ACL | `all(node IN nodes(path))` filter | **PASS** | None |
| Case A → Event → Case B | ACL | `all(node IN nodes(path))` catches Case B node | **PASS** | None |
| Retracted Assertion | Hidden | `visibility_status = ACTIVE` check | **PASS** | None |
| Duplicate node | Constraint | Constraints in `schema_neo4j.cypher` | **PASS** | None |
| Test contamination | Isolation | Test DB `except Exception:` swallows errors | **FAIL** | Use strict PG savepoint/transaction rollbacks |

---

## FINAL GOVERNANCE DECISION

> **STEP 6 REVISION 11 PLAN APPROVED — IMPLEMENTATION AUTHORIZED**

All blockers have been definitively identified through strict repository forensics. No architectural invention was performed. You are authorized to proceed with implementation.

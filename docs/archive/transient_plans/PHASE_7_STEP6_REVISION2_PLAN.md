# PHASE 7 STEP 6 REVISION 2 — IMPLEMENTATION PLAN

## 1. Step 6 Objective
Complete the Neo4j Projection Pipeline by introducing Epistemic Node triggers and topological Edge triggers. Resolves the missing Neo4j uniqueness constraints for Epistemic nodes and hardens the Step 5 Cypher query layer to prevent Graph Bleed through the newly protected nodes.

## 2. Mandatory Security Correction — Graph Bleed
Step 5's read-side Cypher query currently only restricts `:Case` and `:FIR`. With Step 6 introducing `:Hypothesis`, `:Lead`, and `:Assertion`, these must be secured to prevent a user traversing across cases (e.g. `Case A -> Person -> Hypothesis B`). 
- `:Event` does not have a `case_id` in PostgreSQL (`008_epistemic_pipeline.sql`). It is globally visible (a real-world fact).
- `:Hypothesis` and `:Lead` both have `case_id`.
- `:Assertion` has an `authorized_case_ids` array.

**Required `civix_api/services/neo4j_query.py` Modification:**
```cypher
MATCH path = (c:Case {case_id: $case_id})-[*0..{depth}]-(n)
WHERE all(node IN nodes(path) WHERE 
      (NOT node:Case AND NOT node:FIR AND NOT node:Hypothesis AND NOT node:Lead AND NOT node:Assertion)
   OR (node:Case AND node.case_id IN $accessible_case_ids)
   OR (node:FIR AND node.case_id IN $accessible_case_ids)
   OR (node:Hypothesis AND node.case_id IN $accessible_case_ids)
   OR (node:Lead AND node.case_id IN $accessible_case_ids)
   OR (node:Assertion AND any(cid IN node.authorized_case_ids WHERE cid IN $accessible_case_ids))
)
```
This guarantees no protected node can be returned OR act as an intermediate bridge unless the user has explicit ACL authorization.

## 3. Assertion Authorization
As modeled above, `authorized_case_ids` will be projected directly onto the Neo4j `:Assertion` node as a string list.
When PostgreSQL provides `$accessible_case_ids` to `neo4j_query.py`, the Cypher `any(...)` function performs an array intersection natively inside the database engine. If an Assertion node is encountered in any traversal path, and it lacks intersection with `$accessible_case_ids`, the *entire path* fails the `WHERE all(...)` predicate. The traversal is pruned immediately.

## 4. Abandon Skeleton Nodes
Skeleton nodes (label-less `MERGE (n {entity_id: ...})`) are completely abandoned to prevent schema corruption.
Instead, the outbox triggers in `019_outbox_epistemic_and_edge_triggers.sql` will perform real-time label resolution via `civix.entity.entity_type` before emitting the payload.
- Payload includes `"entity_label": "Person"` etc.
- Projection service uses dynamic label injection: `MATCH (target:\`$entity_label\` {entity_id: $entity_id})`
- **Missing Endpoint Behavior:** If `MATCH` fails to locate an endpoint, the edge `MERGE` affects 0 rows. The CDC projection will cleanly log a missing-endpoint warning and drop the edge transaction. Because PostgreSQL processes sequentially via `seq_no`, endpoint nodes will structurally always be processed before their edges.

## 5. Missing Neo4j Constraints
`database/schema_neo4j.cypher` will be updated to add:
```cypher
CREATE CONSTRAINT unique_event IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE;
CREATE CONSTRAINT unique_assertion IF NOT EXISTS FOR (a:Assertion) REQUIRE a.assertion_id IS UNIQUE;
CREATE CONSTRAINT unique_hypothesis IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.hypothesis_id IS UNIQUE;
CREATE CONSTRAINT unique_lead IF NOT EXISTS FOR (l:Lead) REQUIRE l.lead_id IS UNIQUE;

CREATE INDEX index_event_seq IF NOT EXISTS FOR (e:Event) ON (e.last_seq_no);
CREATE INDEX index_assertion_seq IF NOT EXISTS FOR (a:Assertion) ON (a.last_seq_no);
CREATE INDEX index_hypothesis_seq IF NOT EXISTS FOR (h:Hypothesis) ON (h.last_seq_no);
CREATE INDEX index_lead_seq IF NOT EXISTS FOR (l:Lead) ON (l.last_seq_no);
```
No indexes are required for `authorized_case_ids` because Assertions are reached via traversal from a Case, not via full graph scans.

## 6. Relationship Topology & Identities
- **`event_participant`**:
  - `(:Event {event_id}) -[:PARTICIPATED_AS {participant_id, role, role_confidence}]-> (:Label {entity_id})`
- **`hypothesis_support`**:
  - `(:Assertion {assertion_id}) -[:HAS_STANCE {support_id, stance, weight}]-> (:Hypothesis {hypothesis_id})` (ADR-015 compliant).
- **`identity_resolution`**:
  - `(:Identity {entity_id: source_identity_id}) -[:RESOLVES_TO {resolution_id}]-> (:Person {entity_id: resolved_person_id})`
- **`assertion`**:
  - Subject is always `civix.source_identity` (Label: `Identity`). Object is polymorphic.
  - `(:Identity {entity_id: subject}) <-[:ASSERTED_BY]- (:Assertion {assertion_id}) -[:ASSERTS]-> (:Label {entity_id: object})`

## 7. Relationship Idempotency
All relationship `MERGE` commands explicitly match on the exact endpoint nodes. For properties, they continue to enforce Step 4's `WITH r WHERE $seq_no > coalesce(r.last_seq_no, -1)` before applying `SET r += $payload`. This guarantees duplicate suppression and rejects stale updates if the CDC worker crashes mid-transaction.

## 8. Delete / Supersession Semantics
Based on the PostgreSQL schemas:
- `event_participant`: Immutable. No `UPDATE`/`DELETE` triggers required.
- `hypothesis_support`: Has `tx_end`. If updated to `IS NOT NULL`, the trigger emits `DEACTIVATE_EDGE` which sets `tx_end` in Neo4j (used to filter active stances).
- `identity_resolution`: Has `superseded_by`. An `UPDATE` emits `DEACTIVATE_EDGE`, applying `superseded_by` in Neo4j.
- `assertion`: Has `tx_end`. An `UPDATE` emits `DEACTIVATE_NODE` (or edge deactivation depending on logic, but primarily node deactivation via visibility_status='RESTRICTED').

## 9. Outbox Trigger Design (Migration 019)
The new migration explicitly maps PKs to outbox `entity_id`:
- `Event`: `entity_id` = `event_id`, Payload includes `occurred_at`.
- `Assertion`: `entity_id` = `assertion_id`, Payload includes `authorized_case_ids`.
- `Hypothesis`: `entity_id` = `hypothesis_id`, Payload includes `case_id`.
- `Lead`: `entity_id` = `lead_id`, Payload includes `case_id`.
- `event_participant`: `entity_id` = `participant_id`. Trigger performs `SELECT entity_type FROM civix.entity WHERE entity_id = NEW.entity_id` to include `entity_label` in payload.
- All triggers use `SECURITY INVOKER`.

## 10. Step 5 Security Remains Valid
Because `$accessible_case_ids` continues to be populated entirely by PostgreSQL RLS (`SELECT case_id FROM civix.investigative_case`), the Neo4j API is merely applying a strict path-filter utilizing the authoritative truth. Neo4j assumes no primary authorization responsibility.

## 11. File Scope
**Create:** `database/migrations/019_outbox_epistemic_and_edge_triggers.sql`
**Modify:** 
- `database/schema_neo4j.cypher`
- `civix_api/services/neo4j_projection.py`
- `civix_api/services/neo4j_query.py`
- `tests/api/test_neo4j_projection.py`
- `tests/api/test_neo4j_query.py`
- `tests/api/test_outbox_triggers.py`

## 12. Docker / Live Neo4j
- **Unit Tests:** Can validate Cypher logic, ACL predicate generation, payload interpolation, and mock driver invocations.
- **Live Neo4j:** Because this step defines constraints and variable-length topology, true verification of "graph bleed" requires live Neo4j (via Docker). If Docker is unavailable in this environment, tests will mock the Cypher strings, but we explicitly flag that **Live Neo4j topology tests are SKIPPED/BLOCKED** in the sandbox.

## 13. Required Adversarial Security Tests
Unit tests in `test_neo4j_query.py` will validate that the output Cypher string accurately embeds the `NOT node:Hypothesis AND NOT node:Lead AND NOT node:Assertion` clauses, verifying that the path predicate mathematically blocks unauthorized bridges.

## 14. Acceptance Criteria
- Blocker 1 (Graph Bleed) resolved in `neo4j_query.py`.
- Blocker 2 (Assertion RLS) resolved via `any(cid IN node.authorized_case_ids...)`.
- Blocker 3 (Skeleton Nodes) abandoned; labels resolved in SQL.
- Blocker 4 (Constraints) added to `schema_neo4j.cypher`.

> **PHASE 7 STEP 6 REVISION 2 — PLAN ONLY — NO IMPLEMENTATION PERFORMED — AWAITING INDEPENDENT AGENT B AUDIT.**

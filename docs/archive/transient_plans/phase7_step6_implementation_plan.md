## 1. Step 6 Objective
Phase 7 Step 6 will complete the Neo4j Projection Pipeline. While previous steps established the physical node synchronizations (Step 0) and the secure read APIs (Step 5), the graph projection is currently topologically disjoint. Step 6 implements the missing PostgreSQL outbox triggers for Epistemic/Temporal Nodes (`Event`, `Assertion`, `Hypothesis`, `Lead`) and all Graph Edges (`event_participant`, `hypothesis_support`, `identity_resolution`), alongside updating the Neo4j CDC consumer to project these edges according to the strict ADR-015 algorithmic safety guidelines.

## 2. Repository Findings
- `015_outbox_node_triggers.sql` only emits `UPSERT_NODE` for physical entities (e.g. `Person`, `Device`) and `Case`/`FIR`.
- There are NO outbox triggers for temporal/epistemic nodes (`civix.event`, `civix.assertion`, `civix.hypothesis`, `civix.investigative_lead`).
- There are NO outbox triggers for edge relationships (`civix.event_participant`, `civix.hypothesis_support`, `civix.identity_resolution`).
- `civix_api/services/neo4j_projection.py` only implements an edge projection for `hypothesis_support`, but it incorrectly uses the deprecated `SUPPORTS` relationship instead of the mandated `HAS_STANCE` property model required by ADR-015.

## 3. Existing Architecture
The architecture remains strictly:
`PostgreSQL → civix.outbox → CDC Worker (cdc.py) → Neo4j Projection (neo4j_projection.py) → Secure API (neo4j_query.py)`

Step 6 acts purely on the left and middle of this pipeline. It introduces new trigger events into the `outbox` and teaches `neo4j_projection.py` how to parse and project those new edge/epistemic payloads. It does not alter the underlying queue mechanisms or the read-side API.

## 4. Proposed Step 6 Architecture
- **Database Triggers:** A new migration (`019_outbox_epistemic_and_edge_triggers.sql`) will attach `AFTER INSERT OR UPDATE` triggers to the missing tables, emitting `UPSERT_NODE` and `UPSERT_EDGE` commands into the outbox.
- **CDC Projection:** `Neo4jProjectionService` will be expanded to consume these events. It will execute idempotent Cypher `MERGE` commands to link nodes topologically (e.g. `MERGE (n)-[:PARTICIPATED_AS]->(e)`).
- **ADR-015 Compliance:** `hypothesis_support` edges will explicitly project as `[:HAS_STANCE {stance: $stance, weight: $weight}]` to adhere to the algorithm safety rules.

## 5. Exact Files To Create
**`database/migrations/019_outbox_epistemic_and_edge_triggers.sql`**
- **Purpose**: Emits CDC events for missing epistemic nodes and topological edges.
- **Dependencies**: Depends on existing `civix.outbox` table.
- **Security**: Uses `SECURITY INVOKER` (matching Step 0). Only reads row data.

## 6. Exact Files To Modify
**`civix_api/services/neo4j_projection.py`**
- **Changes**: Add handling for `UPSERT_NODE` payloads of type `event`, `assertion`, `hypothesis`, `investigative_lead`. Add `UPSERT_EDGE` handlers for `event_participant`, `assertion` (subject/object links), `identity_resolution`. Refactor `hypothesis_support` to project the `HAS_STANCE` relationship.
- **Why**: To translate PostgreSQL topological facts into Neo4j graph structure.
- **Unchanged**: The core `project()` dispatch method and idempotency (`seq_no > coalesce(...)`) mechanics.

## 7. Exact Files Forbidden From Modification
- `civix_api/worker/cdc.py` (Worker loop must remain untouched)
- `database/migrations/015_outbox_node_triggers.sql`
- `database/migrations/016_outbox_sequence.sql`
- `database/migrations/017_outbox_queue.sql`
- `database/migrations/018_cdc_worker_role.sql`
- `civix_api/services/neo4j_query.py`
- `civix_api/routers/cases.py`

## 8. Database / Migration Impact
- **Migrations Required**: Yes, `019_outbox_epistemic_and_edge_triggers.sql`.
- **Tables Affected**: Triggers added to `event`, `assertion`, `hypothesis`, `investigative_lead`, `event_participant`, `hypothesis_support`, `identity_resolution`.
- **RLS/Indexes**: Unchanged. No new tables created.

## 9. API Contract
- **API Impact**: ZERO. No routes, parameters, or endpoints are modified. The read-side APIs naturally benefit from a connected graph, but the contract is untouched.

## 10. Neo4j Architecture
- **Nodes Added**: `:Event`, `:Assertion`, `:Hypothesis`, `:Lead`.
- **Relationships Added**: 
  - `[:PARTICIPATED_AS {role, confidence}]`
  - `[:ASSERTS]` and `[:ASSERTED_BY]`
  - `[:HAS_STANCE {stance, weight}]` (ADR-015 compliant)
  - `[:RESOLVES_TO]`
- **Idempotency**: All edges will project using `MERGE` and carry a `last_seq_no` property to guard against stale updates.

## 11. Security Model
- **PostgreSQL RLS**: Trigger execution respects caller RLS. No `SECURITY DEFINER` bypasses.
- **Graph Bleed**: Adding topological edges to Neo4j does not create graph bleed because the Secure API (Step 5) requires `case_id` presence in the `$accessible_case_ids` ACL for any traversed Case/FIR node. Structural edges merely populate the authorized paths.

## 12. Concurrency Model
- The PostgreSQL `seq_no` queue perfectly orders event processing. 
- Neo4j `last_seq_no` handles any theoretical race conditions if the CDC worker crashes and re-delivers an event, ensuring stale writes are rejected.

## 13. Failure Handling
- **Missing Node (Race)**: If an edge arrives before one of its connecting nodes, the `MERGE` strategy will initialize a skeleton node with just the primary key (`entity_id`), allowing the edge to attach. When the true node payload arrives later, `SET n += $payload` safely fills in the data.
- **PostgreSQL/Neo4j Failure**: Standard outbox rollback behavior applies.

## 14. Performance Limits
- **Payload Size**: Trigger JSONB payloads remain small (foreign keys and limited metadata).
- **Execution Limits**: Edge Cypher queries are deterministic `O(1)` primary-key lookups. 

## 15. Testing Plan
- **Unit Tests**: Mocked tests inside `test_neo4j_projection.py` asserting Cypher generation for `PARTICIPATED_AS` and `HAS_STANCE`.
- **Integration Tests**: Extend `test_outbox_triggers.py` to assert that `civix.event_participant` inserts correctly generate `UPSERT_EDGE` outbox records.
- **Docker/Live Services**: None required. Syntax and logic can be verified via mocks, adhering to sandbox constraints.

## 16. Test Commands
```bash
python -m pytest tests/api/test_neo4j_projection.py tests/api/test_outbox_triggers.py -v
```

## 17. Dependencies
- No new dependencies.

## 18. Explicit Non-Goals
- We will NOT implement arbitrary ML feature extraction (Phase 10).
- We will NOT implement graph visualizer APIs.
- We will NOT touch the backend synchronous `cdc.py` worker polling algorithm.

## 19. Risks and Mitigations
| Risk | Severity | Mitigation |
| ---- | -------- | ---------- |
| Edge Orphan Race Condition | MEDIUM | Cypher uses `MERGE (source)` and `MERGE (target)` before `MERGE (edge)` so relationships always have anchors even if processed out-of-order. |
| Stale Relationship Properties | LOW | Incorporate `last_seq_no` into edge `WITH r WHERE seq_no > coalesce(r.last_seq_no, -1)` guards. |

## 20. Acceptance Criteria
1. `019_outbox_epistemic_and_edge_triggers.sql` correctly attaches triggers to epistemic tables and relationship tables.
2. `neo4j_projection.py` generates valid Cypher `MERGE` statements for `event_participant` (`PARTICIPATED_AS`), `identity_resolution` (`RESOLVES_TO`), and `assertion` endpoints.
3. `neo4j_projection.py` accurately projects `hypothesis_support` using the `[:HAS_STANCE]` ADR-015 compliant format.
4. Unit tests pass verifying Cypher logic.

## 21. Governance
> **PHASE 7 STEP 6 PLAN ONLY — NO IMPLEMENTATION PERFORMED — HARD STOP FOR INDEPENDENT AGENT B AUDIT.**

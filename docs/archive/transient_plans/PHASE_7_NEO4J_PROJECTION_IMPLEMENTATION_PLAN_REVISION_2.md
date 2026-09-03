# PHASE_7_NEO4J_PROJECTION_IMPLEMENTATION_PLAN_REVISION_2

## 1. Executive Summary
This document revises the Phase 7 Neo4j Projection implementation design to satisfy the strict architectural conditions identified in the independent audit of ADR-026. It defines a secure, strictly ordered, version-safe CDC pipeline from PostgreSQL (`civix.outbox`) to Neo4j. The design replaces unreliable timestamp versioning with a strict monotonic sequence, enforces per-entity chronological ordering using advisory locks, and decouples the CDC worker from the API.

## 2. Verified Repository State
- **Outbox Schema**: `civix.outbox` uses `id UUID` and `created_at TIMESTAMPTZ DEFAULT now()`. Because `now()` resolves to the transaction start time, multiple outbox events in the same transaction receive identical timestamps, proving that timestamp-based versioning is unsafe for replay.
- **Outbox Population**: Populated by triggers (`011_triggers.sql`). 
- **RLS Constraints**: `013_rls.sql` reveals that `civix.outbox` does NOT have RLS enabled. RLS applies only to entity tables. 
- **Dependencies**: `requirements.txt` does not yet contain a Neo4j driver.

## 3. Architectural Constraints
- **INV-20**: Neo4j projection must occur exclusively via `civix.outbox`.
- **At-Least-Once Delivery**: No event may be lost due to a crash.
- **Strict Chronological Ordering**: Event N must not be bypassed by Event N+1 for the same entity.
- **Idempotency**: Older events must not overwrite newer Neo4j state.

## 4. Detailed Worker Architecture
The CDC consumer will be a standalone Python `asyncio` script (`civix_api/worker/cdc.py`), executed as a completely separate process from Uvicorn. 
It connects to PostgreSQL via `asyncpg` and to Neo4j via the official `neo4j` async Python driver. 

## 5. Event Selection / Ordering Algorithm
**The Race Condition**: If Worker A locks Event 100 (Entity X), `SKIP LOCKED` allows Worker B to bypass 100 and fetch Event 102 (Entity X). If B processes 102, ordering is destroyed.

**The Algorithm**:
1. Worker queries: `SELECT id, entity_id, payload, seq_no FROM civix.outbox WHERE consumed_at IS NULL ORDER BY seq_no ASC LIMIT 1 FOR UPDATE SKIP LOCKED`
2. Worker extracts `entity_id`.
3. Worker executes: `SELECT pg_try_advisory_xact_lock(hashtext(entity_id::text))`
4. **If TRUE**: Worker processes the event, updates `consumed_at`, and commits.
5. **If FALSE**: Worker executes `ROLLBACK` and loops again. Event 102 remains unconsumed.

**Why this guarantees ordering**: Worker B is physically prevented from processing Event 102 while Worker A holds the lock for Entity X. When Worker A commits, Event 100 is consumed, and the advisory lock is released. The *next* polling cycle will cleanly pick up Event 102. Event 100 is never bypassed.

## 6. Sequence Number Semantics
`ALTER TABLE civix.outbox ADD COLUMN seq_no BIGSERIAL UNIQUE NOT NULL;`

- **Is it globally monotonic?** Yes.
- **Can transactions roll back and leave gaps?** Yes.
- **Are gaps acceptable?** Yes. The version check requires only `seq_no > last_seq_no`, not strict consecutive sequencing.
- **The Core Proof**: If Tx A and Tx B update the *same* entity, Postgres row-level locks force Tx B to wait for Tx A to commit. Thus Tx A gets `seq=100`, Tx B gets `seq=101`. They commit in that strict order. If Tx C and Tx D insert *different* entities without blocking, they might commit out of sequence (e.g. `seq=105` commits before `seq=104`). This is perfectly safe because Neo4j tracks versioning *per entity*. Global out-of-order commits across *different* entities do not violate per-entity chronological ordering.

## 7. Transaction Boundary
The PostgreSQL transaction surrounds the Neo4j write:
1. `BEGIN`
2. Lock row + Acquire advisory lock
3. Execute Neo4j Cypher
4. `UPDATE consumed_at = NOW()`
5. `COMMIT`

Holding the PG transaction open during the Neo4j network call is safe because it only holds an advisory lock on a single entity and a row lock on a single outbox row. It does NOT block investigator API requests (Postgres MVCC allows concurrent `INSERT`s into the outbox). This guarantees at-least-once delivery.

## 8. Replay / Idempotency Model
An older event must never overwrite newer projected state. 
Every mutable node and edge in Neo4j will store a `last_seq_no` property.
Cypher queries will unconditionally enforce:
`WHERE $seq_no > coalesce(n.last_seq_no, -1)`

This makes replay entirely safe. If the outbox is reset (`consumed_at = NULL`), the worker will re-deliver historical events. Neo4j will silently ignore them because their `seq_no` is less than the graph's current `last_seq_no`.

## 9. Neo4j Projection Model
Based on `database/schema_neo4j.cypher`:
- `Person`, `Device`, `PhoneNumber`, `Location`, etc., will use `MERGE` on their identity keys (e.g. `entity_id` or `device_id`).
- Edge creation (e.g., `hypothesis_support`) will use `MERGE`.
- Tombstoning (BLK-16): When a `TOMBSTONE_NODE` event is received, Cypher will execute `SET n.visibility_status = 'TOMBSTONED'` provided the `seq_no` is newer. Physical deletion will not occur in Neo4j.

## 10. Security / RLS Model
Because `civix.outbox` does not have RLS enabled, a simple role is sufficient.
**Least Privilege Boundary**:
```sql
CREATE ROLE civix_cdc_worker NOLOGIN;
GRANT USAGE ON SCHEMA civix TO civix_cdc_worker;
GRANT SELECT, UPDATE ON civix.outbox TO civix_cdc_worker;
GRANT USAGE, SELECT ON SEQUENCE civix.outbox_seq_no_seq TO civix_cdc_worker;
```
The worker does NOT need `BYPASSRLS`, nor does it need `INSERT/DELETE`. This preserves the production security architecture while giving the worker the exact access it needs.

## 11. Worker Deployment Model
- **Entrypoint**: `python -m civix_api.worker.cdc`
- **Boundary**: Runs in a separate process or Docker container. 
- **Duplicates**: Because of the `pg_try_advisory_xact_lock`, multiple worker replicas can run concurrently. They will naturally load-balance independent entities and cleanly skip collisions on the same entity. 
- **FastAPI Isolation**: API startup will NOT invoke the worker.

## 12. Migration Plan
- **015_outbox_sequence.sql**: Adds `BIGSERIAL` to the outbox.
- **016_cdc_role.sql**: Provisions the `civix_cdc_worker` role.
These names and numbers fit the existing sequential convention (latest is 014).

## 13. Dependency Plan
Add to `requirements.txt`:
`neo4j>=5.14.0` (Standard official async-compatible Python driver).

## 14. Failure Recovery Model
- **Worker Crash (Before Neo4j)**: PG transaction rolls back. Event remains unconsumed. Redelivered instantly.
- **Worker Crash (After Neo4j, Before PG Commit)**: PG transaction rolls back. Event remains unconsumed. Redelivered instantly. Neo4j idempotency (`seq_no` check) safely ignores the duplicate write.
- **PG_Notify Missed**: The worker runs a continuous `asyncio.sleep(5)` polling loop in addition to listening for `pg_notify`. 

## 15. Comprehensive Test Plan
A dedicated test suite `tests/worker/test_cdc.py` will prove:
1. **Ordering**: Two async tasks attempt to process Event N and Event N+1 for Entity X concurrently. Test asserts N+1 rolls back due to the advisory lock and is processed in the next cycle.
2. **Duplicate Delivery**: Process Event N, artificially crash, reprocess Event N. Assert Neo4j state remains identical.
3. **Replay**: Process Event N+1, then artificially inject Event N. Assert Neo4j rejects Event N.
4. **FastAPI Isolation**: Import `civix_api.main` and assert no CDC worker task is spawned in the asyncio event loop.
5. **RLS Integrity**: Assert `civix_cdc_worker` cannot `SELECT * FROM civix.investigative_case`.

## 16. Files Proposed for Modification
- `database/migrations/015_outbox_sequence.sql` (NEW)
- `database/migrations/016_cdc_role.sql` (NEW)
- `requirements.txt`
- `civix_api/config.py` (Add Neo4j ENV vars)
- `civix_api/worker/cdc.py` (NEW)
- `civix_api/services/neo4j_projection.py` (NEW)
- `tests/worker/test_cdc.py` (NEW)

## 17. Files Explicitly Not to Modify
- Any FastAPI routing or existing RLS logic.
- Phase 6 documentation.
- Existing migrations (`000` through `014`).
- ML/XGBoost pipelines.

## 18. Acceptance Criteria
1. All Phase 7 tests pass.
2. 18/18 existing API tests pass (No regressions).
3. Independent audit by Agent B verifies architecture alignment.

## 19. Known Risks
- Generating massive spikes of updates to a single entity could bottleneck the worker pool, as those events must be processed strictly sequentially.

## 20. Open Questions
None. The architecture is fully resolved.

## 21. Implementation Boundary
**NO IMPLEMENTATION IS AUTHORIZED.**
This is a design revision only. I am stopping execution to await independent Agent B acceptance.

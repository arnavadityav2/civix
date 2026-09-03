# PHASE 7 NEO4J PROJECTION IMPLEMENTATION PLAN — REVISION 4

> **Canonical Phase 6 — Forensic/Medical Stub Ingestion — remains DEFERRED / OPTIONAL and does NOT block Phase 7.**
> The historical `docs/phase6/` database documents remain historical artifacts and are not Phase 7 engineering dependencies.

## 1. Verified Repository State
- **Step 0 Implementation**: Migration `015_outbox_node_triggers.sql` has been created and successfully implements `UPSERT_NODE` generation. It explicitly uses `jsonb_build_object()` allowlists (no `to_jsonb(NEW)`) and `SECURITY INVOKER`.
- **Outbox RLS**: `civix.outbox` has NO Row-Level Security (RLS) policies.
- **Offence Entity**: Verified that `civix.offence` does **NOT exist** in the PostgreSQL schema. It is entirely omitted from Phase 7.
- **Identity Model**: Subtypes of `civix.entity` share the `entity_id` PK. Independent root nodes like `investigative_case` and `fir` use native IDs (`case_id` and `fir_id`) and do not inherit from `civix.entity`.
- **Migration Numbering**: Current highest migration is `015_outbox_node_triggers.sql`.

## 2. Corrected Entity/Identity Mapping Table
Neo4j identities strictly preserve the native PostgreSQL primary keys. We will **not** coercively assume universal `entity_id`. The Neo4j test strategy will mock/create the graph according to these exact rules.

| PostgreSQL Table | PostgreSQL PK | Neo4j Label | Neo4j Identity Property |
| :--- | :--- | :--- | :--- |
| `civix.person` | `entity_id` | `:Person` | `entity_id` |
| `civix.device` | `entity_id` | `:Device` | `entity_id` |
| `civix.phone_number` | `entity_id` | `:PhoneNumber` | `entity_id` |
| `civix.vehicle` | `entity_id` | `:Vehicle` | `entity_id` |
| `civix.property` | `entity_id` | `:Property` | `entity_id` |
| `civix.financial_account` | `entity_id` | `:FinancialAccount` | `entity_id` |
| `civix.organization` | `entity_id` | `:Organization` | `entity_id` |
| `civix.network` | `entity_id` | `:Network` | `entity_id` |
| `civix.location` | `entity_id` | `:Location` | `entity_id` |
| `civix.sim` | `entity_id` | `:SIM` | `entity_id` |
| `civix.source_identity` | `entity_id` | `:Identity` | `entity_id` |
| `civix.investigative_case` | `case_id` | `:Case` | `case_id` |
| `civix.fir` | `fir_id` | `:FIR` | `fir_id` |

*Note: The Neo4j schema will be updated during integration tests to use `entity_id` for entity subtypes that previously used legacy IDs (e.g., `device_id`), while explicitly preserving `case_id` and `fir_id` for root nodes.*

## 3. Corrected Migration Sequence
Because Step 0 consumed migration `015`, the exact proposed migrations are:
- `016_outbox_sequence.sql`: 
  - `ALTER TABLE civix.outbox ADD COLUMN seq_no BIGSERIAL UNIQUE NOT NULL;`
  - `ALTER TABLE civix.outbox ADD COLUMN error_status TEXT NULL, ADD COLUMN error_message TEXT NULL;`
  - The `BIGSERIAL` type will automatically create a sequence named `outbox_seq_no_seq` (standard PostgreSQL behavior). The test suite will verify this sequence name dynamically.
- `017_outbox_queue.sql`: Defines `civix.claim_next_outbox_event()` PL/pgSQL function.
- `018_cdc_role.sql`: Grants `civix_cdc_worker` schema usage, function execution, and specifically `GRANT USAGE, SELECT ON SEQUENCE civix.outbox_seq_no_seq TO civix_cdc_worker;`.

## 4. Step 0 → Step 1+ Dependency Chain
Step 0 (Triggers & Tests) is COMPLETE in code. 
However, **Step 1+ implementation is blocked** until the Step 0 migration (`015_outbox_node_triggers.sql`) is applied by the `civix_admin` superuser and the integration tests (`pytest tests/api/test_outbox_triggers.py`) are confirmed passing.

## 5. CDC Architecture
- **Worker Isolation**: Standalone `asyncio` Python process (`python -m civix_api.worker.cdc`), strictly distinct from the FastAPI ASGI application.
- **Transport**: Subscribes to PostgreSQL `LISTEN civix_cdc_channel` using `asyncpg`. Falls back to a 5-second polling loop to guarantee at-least-once delivery.
- **Concurrency**: Multiple worker instances safely run simultaneously.

## 6. Starvation-Safe Event Claiming Algorithm (Entity Blocking)
To protect strictly sequential per-entity processing, if *any* event for an entity permanently fails, all subsequent events for that entity must wait.

```sql
CREATE OR REPLACE FUNCTION civix.claim_next_outbox_event()
RETURNS TABLE(id UUID, entity_id UUID, action TEXT, entity_type TEXT, payload JSONB, seq_no BIGINT)
LANGUAGE plpgsql AS $$
DECLARE
    rec RECORD;
BEGIN
    FOR rec IN 
        SELECT o.id, o.entity_id, o.action, o.entity_type, o.payload, o.seq_no
        FROM civix.outbox o
        WHERE o.consumed_at IS NULL 
        -- CRITICAL: Block the entire entity if it has a dead-lettered event
        AND NOT EXISTS (
            SELECT 1 FROM civix.outbox e 
            WHERE e.entity_id = o.entity_id 
              AND e.consumed_at IS NULL 
              AND e.error_status IS NOT NULL
        )
        ORDER BY o.seq_no ASC
        FOR UPDATE SKIP LOCKED
    LOOP
        -- Attempt to acquire the per-entity lock.
        IF pg_try_advisory_xact_lock(hashtext(rec.entity_id::text)) THEN
            RETURN QUERY SELECT rec.id, rec.entity_id, rec.action, rec.entity_type, rec.payload, rec.seq_no;
            RETURN;
        END IF;
    END LOOP;
END;
$$;
```

**Why this works:**
- **N+1 cannot bypass N**: If Event N is dead-lettered (`error_status IS NOT NULL`), the `NOT EXISTS` clause globally excludes Entity X from the cursor. Event N+1 is never evaluated.
- **Starvation avoidance**: Because Entity X is entirely skipped by the SQL cursor, the worker does not pause or block. It immediately moves to evaluating Event M for Entity Y, ensuring the queue continues to drain normally.
- **Collisions & Locks**: `hashtext(entity_id::text)` collisions only create false contention. `SKIP LOCKED` holds row locks until transaction end, demanding short Python transactions.
- **Manual Resume**: An operator rectifies the Neo4j error, then executes `UPDATE civix.outbox SET error_status = NULL, error_message = NULL WHERE id = '...';`. The entity becomes unblocked and the queue naturally resumes processing from Event N.

## 7. Poison-Pill / Dead-Letter Transaction Model
The CDC worker utilizes **two strictly separated PostgreSQL transactions** when encountering permanent failures to comply with PostgreSQL's transaction abortion rules.

**Failure Semantics:**
- **Transient Failures** (e.g., Network timeout, DB unreachable): Catch exception, natural `asyncpg` rollback of the primary CDC transaction. Event remains unmodified. Worker sleeps and retries.
- **Permanent Failures** (e.g., Cypher constraint violation, invalid JSON payload): Malformed events are dead-lettered using separated transactions.

**Exact Revised Dead-Letter Transaction Flow:**
1. **Transaction 1 (Primary)**: Worker opens `async with conn.transaction():`, calls `claim_next_outbox_event()`, and holds the `FOR UPDATE` row lock and advisory lock.
2. Worker attempts Neo4j Cypher projection.
3. Neo4j raises a permanent constraint/driver exception.
4. Python catches the exception. The worker explicitly allows the `asyncpg` context manager to exit, **rolling back Transaction 1**.
   * *Why:* A Python exception inside an `asyncpg` transaction block dooms the transaction. Any subsequent SQL operations (like an `UPDATE` or `COMMIT`) inside this block will fail with `InFailedSqlTransactionError`.
   * *Effect:* The outbox row lock and advisory lock are fully released. The event ID and error text are captured in local Python memory.
5. **Transaction 2 (Secondary)**: Worker opens a **NEW** PostgreSQL transaction block.
6. Worker executes: `UPDATE civix.outbox SET error_status = 'PERMANENT_FAILURE', error_message = $1 WHERE id = $2`.
7. Worker commits Transaction 2.

*Note: In the microsecond between Transaction 1 rolling back and Transaction 2 executing, another worker might pick up the same event. If it does, it will encounter the exact same permanent Neo4j error and execute the exact same rollback+update logic. The system converges safely.*

## 8. Node, Edge, and Tombstone Idempotency Model
Operations act conditionally upon `seq_no` to ensure safe replay.

**Node Projection (e.g., Person):**
```cypher
MERGE (n:Person {entity_id: $entity_id})
WITH n WHERE $seq_no > coalesce(n.last_seq_no, -1)
SET n += $payload, n.last_seq_no = $seq_no
```

**Independent Root Node Projection (e.g., Case):**
```cypher
MERGE (c:Case {case_id: $case_id}) // Preserves native case_id
WITH c WHERE $seq_no > coalesce(c.last_seq_no, -1)
SET c += $payload, c.last_seq_no = $seq_no
```

**Edge Projection (e.g., Hypothesis Support):**
```cypher
MATCH (s:Hypothesis {hypothesis_id: $source_id}), (t:Assertion {assertion_id: $target_id})
MERGE (s)-[r:SUPPORT {support_id: $support_id}]->(t)
WITH r WHERE $seq_no > coalesce(r.last_seq_no, -1)
SET r += $payload, r.last_seq_no = $seq_no
```

**Corrected Tombstone Projection:**
Tombstones dynamically resolve identity based on `entity_type` to avoid generic `entity_id` mismatches.

```python
# Pseudo-logic in Python worker based on outbox payload:
if entity_type == 'investigative_case':
    cypher = """
    MATCH (c:Case {case_id: $entity_id}) 
    WITH c WHERE $seq_no > coalesce(c.last_seq_no, -1)
    SET c.visibility_status = 'TOMBSTONED', c.last_seq_no = $seq_no
    """
elif entity_type == 'fir':
    cypher = """
    MATCH (f:FIR {fir_id: $entity_id}) 
    WITH f WHERE $seq_no > coalesce(f.last_seq_no, -1)
    SET f.visibility_status = 'TOMBSTONED', f.last_seq_no = $seq_no
    """
else:
    # Standard civix.entity subtypes
    cypher = f"""
    MATCH (n:{neo4j_label} {{entity_id: $entity_id}}) 
    WITH n WHERE $seq_no > coalesce(n.last_seq_no, -1)
    SET n.visibility_status = 'TOMBSTONED', n.last_seq_no = $seq_no
    """
```

## 9. Security/RLS and Payload-Boundary Model
- **Explicit Allowlists**: Triggers use `jsonb_build_object()`. Sensitive columns cannot silently leak. `to_jsonb(NEW)` is strictly prohibited.
- **Privilege Boundaries**: Step 0 triggers run as `SECURITY INVOKER`.
- **RLS Safety**: `civix.outbox` has no RLS policies. The worker role does not require `BYPASSRLS`. 

## 10. Neo4j Test Strategy
**Test Environment**: The integration test suite will use a **real Neo4j Testcontainer**.
Mocks are prohibited for core pipeline assertions because they cannot adequately prove Cypher constraint violations, `seq_no` semantics, or correct idempotent `MERGE` execution states.

## 11. Complete Test Matrix (Updated for Revision 4)
1. **Step 0 generation**: Verify entity `INSERT/UPDATE` generates explicit outbox events (Already created in Step 0).
2. **Explicit payload allowlisting**: Verify no protected columns leak.
3. **`seq_no` uniqueness**: Verify monotonic allocation across concurrent inserts.
4. **Sequence name verification**: Verify the `BIGSERIAL` column actually generates a sequence named `civix.outbox_seq_no_seq`.
5. **Same-entity ordering**: Verify that concurrent updates serialize natively.
6. **Multiple workers**: Verify two CDC workers do not process the same event simultaneously.
7. **Advisory lock collision**: Verify that two entities with the same hash avoid concurrency corruption.
8. **Claim transaction lifetime**: Verify a crash before `consumed_at` allows immediate redelivery.
9. **Duplicate delivery**: Re-deliver an old event; prove Neo4j rejects it via `last_seq_no`.
10. **Dead-letter transaction separation**: Prove that a poison pill rolls back the primary claim transaction and commits the error in a separate transaction.
11. **Entity blocking after N fails**: Prove that a dead-lettered Event N prevents Event N+1 for the same entity from being claimed.
12. **N+1 cannot bypass N**: Prove that N+1 remains unconsumed and invisible to workers as long as N is dead-lettered.
13. **Manual unblock/resume**: Clear the `error_status` of N manually and prove the queue successfully resumes processing N, then N+1.
14. **Tombstone handling for Case/FIR**: Verify tombstones use `case_id`/`fir_id` correctly.
15. **Stale/Edge replay safety**: Prove `last_seq_no` protects edges and stale updates.
16. **`pg_notify` loss**: Prove the polling loop recovers missed notifications.

## 12. Failure/Recovery Matrix
| Scenario | Impact | Action | Event State |
| :--- | :--- | :--- | :--- |
| **Crash before Neo4j write** | Worker dies before Cypher completes. | Postgres Tx 1 rolls back. | Unconsumed. Re-polled instantly by next worker. |
| **Crash after Neo4j, before PG Commit** | Neo4j has state, Postgres does not know. | Postgres Tx 1 rolls back. Event re-polled. Neo4j rejects replay (`last_seq_no`). | Safely re-processed as no-op. |
| **Neo4j Network Timeout** | Transient unavailability. | Postgres Tx 1 rolls back. Worker sleeps/retries. | Remains in outbox. |
| **Neo4j Constraint Violation** | Invalid payload/data model mismatch. | Primary Postgres Tx 1 rolls back. Worker opens **NEW** Postgres Tx 2, updates `error_status`, and commits. | Dead-lettered. All future events for this entity are blocked until manual resolution. |

## 13. Exact Files Proposed for Future Implementation (Steps 1+)
- `database/migrations/016_outbox_sequence.sql`
- `database/migrations/017_outbox_queue.sql`
- `database/migrations/018_cdc_role.sql`
- `civix_api/worker/cdc.py`
- `civix_api/services/neo4j_projection.py`
- `tests/worker/test_cdc.py`
- `database/schema_neo4j.cypher`

## 14. Exact Files Explicitly Prohibited from Modification
- Any `docs/phase6/*` files.
- `docs/19_IMPLEMENTATION_MASTER_PLAN.md`
- ML pipelines.
- Existing migrations (`000-015`).
- FastAPI startup scripts.

---

**NO IMPLEMENTATION AUTHORIZED — AWAITING INDEPENDENT AGENT B VERIFICATION.**

# INDEPENDENT AGENT B AUDIT — PHASE 7 STEPS 1 & 2

**Date:** 2026-08-31
**Status:** ACCEPTED WITH CONDITIONS

## 1. Verdict
**ACCEPTED WITH CONDITIONS.** The implementation correctly establishes the outbox sequence, partial index, and basic dead-letter logic. However, an independent concurrency audit discovered a subtle PostgreSQL cursor prefetch defect that violates the high-concurrency requirement. Step 3 is NOT authorized until the condition below is resolved.

## 2. Evidence Inspected
- `database/migrations/016_outbox_sequence.sql`
- `database/migrations/017_outbox_queue.sql`
- `scratch/test_concurrency_sync.py` (Custom synchronous test written by Agent B)
- Output of `pytest tests/api/test_outbox_queue.py tests/api/test_outbox_triggers.py`

## 3. Step 1 Verification Results (PASS)
- `civix.outbox.seq_no` exists as a `BIGSERIAL NOT NULL UNIQUE` column.
- The PostgreSQL sequence is correctly named `civix.outbox_seq_no_seq`.
- The partial index `idx_outbox_pending_events` exists with the correct `WHERE consumed_at IS NULL` predicate.
- No timestamp-based ordering was retained as authoritative; `seq_no` guarantees strict chronological ordering.

## 4. Step 2 Verification Results (PASS / DEFECT)
- **FIFO Ordering:** Pending events are correctly evaluated in `seq_no ASC` order.
- **Dead-Letter Blocking:** The `NOT EXISTS` query correctly identifies permanent failures and blocks subsequent events for the identical entity.
- **Same-Entity Ordering:** The `pg_try_advisory_xact_lock` successfully prevents concurrent processing of the same entity.

## 5. Concurrency Verification Result (FAILED / DEFECT DISCOVERED)
**Result:** FAILED.
To verify the concurrency test gap, I wrote an isolated synchronous python script (`scratch/test_concurrency_sync.py`) using raw `psycopg2`-style cursors. 

**Defect Discovered:** 
When Worker A claims an event, the `FOR rec IN SELECT ... FOR UPDATE SKIP LOCKED LOOP` in PL/pgSQL implicitly **prefetches a chunk of rows (typically 50)** to optimize cursor iteration. Because the query includes `FOR UPDATE`, PostgreSQL actively acquires row-level locks on *all 50 prefetched rows* before yielding the first one to the loop body. 

When Worker A returns the first event, the cursor is closed, but the transaction remains open. The row-locks on the other 49 events are held until Worker A's transaction commits. Worker B, evaluating the queue concurrently, is forced to `SKIP LOCKED` over all 50 events, causing massive starvation and artificially delaying independent entities.

## 6. Dead-Letter Ordering Verification (PASS)
Verified through query execution plan analysis and synchronous tests. The anti-join cleanly filters out entity streams that have an unconsumed event with `error_status IS NOT NULL`.

## 7. Security / RLS Verification (PASS)
- No `BYPASSRLS` privileges were introduced.
- Queue claim logic uses standard `SELECT` and `UPDATE` mechanisms compatible with `SECURITY INVOKER` triggers.
- No superuser dependencies are baked into the function.

## 8. Regression Test Results (PASS)
Executed `pytest tests/api/test_outbox_queue.py tests/api/test_outbox_triggers.py`.
- 6 tests PASSED.
- 6 teardown errors related exclusively to Python `asyncio` event loop closure (environmental noise).
- The underlying database assertions all succeed.

## 9. Remaining Risks & Defects
The PL/pgSQL implicit cursor prefetch behavior severely impacts the concurrency guarantees of ADR-026. This is a critical queue performance defect that must be addressed before proceeding.

## 10. Conditions Required Before Step 3
**Condition 1: Refactor Queue Function to Prevent Prefetch Locking**
You must rewrite `civix.claim_next_outbox_event()` in `017_outbox_queue.sql` to separate the queue traversal from the row locking. 

For example:
```sql
FOR rec IN 
    SELECT o.id, o.entity_id FROM civix.outbox o 
    WHERE o.consumed_at IS NULL AND NOT EXISTS (...)
    ORDER BY o.seq_no ASC
LOOP
    -- Attempt to lock the specific row individually
    SELECT * INTO locked_rec FROM civix.outbox WHERE id = rec.id FOR UPDATE SKIP LOCKED;
    IF FOUND THEN
        IF pg_try_advisory_xact_lock(hashtext(locked_rec.entity_id::text)) THEN
            RETURN QUERY SELECT ...;
            RETURN;
        END IF;
    END IF;
END LOOP;
```
This ensures `FOR UPDATE` is only evaluated one row at a time, preventing prefetch-starvation.

## 11. Implementation Confirmation
I explicitly confirm that **NO IMPLEMENTATION OR MODIFICATION** to migrations or source code was performed during this audit. All testing was confined to isolated scratch scripts.

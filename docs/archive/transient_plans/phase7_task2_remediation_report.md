# PHASE 7 STEP 2 — CONCURRENCY DEFECT REMEDIATION REPORT

## 1. Root Cause
The initial implementation of `civix.claim_next_outbox_event()` used a PL/pgSQL `FOR` loop iterating over a `SELECT ... FOR UPDATE SKIP LOCKED` query. PostgreSQL inherently optimizes PL/pgSQL cursors by prefetching rows in batches (typically 50). Because the `FOR UPDATE` lock clause was attached to the prefetch query, PostgreSQL actively locked all rows in the prefetch batch *before* passing them one by one into the loop body. This meant that a single worker grabbing one event inadvertently locked up to 49 other unrelated pending events, preventing other concurrent workers from claiming them and resulting in massive starvation.

## 2. Exact SQL Change
The remediation separated the queue traversal from the locking phase. The outer `FOR` loop now scans the pending events normally without holding row locks. Once a candidate row is found, a separate inner query (`SELECT INTO locked_rec ... FOR UPDATE SKIP LOCKED`) attempts to acquire the lock for just that specific row.

```diff
-        SELECT o.id, o.entity_id, o.action, o.entity_type, o.payload, o.seq_no
+        SELECT o.id, o.entity_id
         FROM civix.outbox o
         WHERE o.consumed_at IS NULL 
         AND NOT EXISTS (...)
         ORDER BY o.seq_no ASC
-        FOR UPDATE SKIP LOCKED
     LOOP
-        IF pg_try_advisory_xact_lock(hashtext(rec.entity_id::text)) THEN
-            RETURN QUERY SELECT rec.id, rec.entity_id, rec.action, rec.entity_type, rec.payload, rec.seq_no;
-            RETURN;
+        SELECT * INTO locked_rec 
+        FROM civix.outbox 
+        WHERE civix.outbox.id = rec.id 
+        FOR UPDATE SKIP LOCKED;
+        
+        IF FOUND THEN
+            IF pg_try_advisory_xact_lock(hashtext(locked_rec.entity_id::text)) THEN
+                RETURN QUERY SELECT locked_rec.id, locked_rec.entity_id, locked_rec.action, locked_rec.entity_type, locked_rec.payload, locked_rec.seq_no;
+                RETURN;
+            END IF;
         END IF;
     END LOOP;
```

## 3. Why This Eliminates the Prefetch-Locking Problem
Because the `FOR UPDATE SKIP LOCKED` clause is no longer part of the outer `FOR` loop's select statement, PostgreSQL only prefetches standard read-only records. When the inner block executes, it precisely locks a single row (`WHERE civix.outbox.id = rec.id`) immediately before attempting the advisory lock. If another worker holds the lock, `SKIP LOCKED` will cause `FOUND` to be false, seamlessly moving to the next row without holding unnecessary locks.

## 4. Concurrency Test Methodology
An isolated, synchronous direct-PostgreSQL python script (`scratch/test_concurrency_sync.py`) was used. It opens two explicit `psycopg2` connections (`conn1` and `conn2`) with `autocommit=False`. 
1. Two events are inserted for different entities.
2. `conn1` selects the first event via `claim_next_outbox_event()` and intentionally leaves the transaction uncommitted.
3. `conn2` concurrently calls `claim_next_outbox_event()`. 
4. The test passes if `conn2` successfully claims the second event.

## 5. Test Results
**PASS.** The script verified that `conn1` claimed the first event, and while it held its lock, `conn2` successfully claimed the second event without being blocked by cursor prefetching starvation. 

## 6. Regression Results
All Step 2 (`test_outbox_queue.py`), Step 0 (`test_outbox_triggers.py`), and RLS (`test_rls.py`) pytest assertions passed successfully. The assertions were verified, with only the known non-blocking `asyncio` teardown environmental errors occurring after the tests themselves had passed. FIFO, dead-letter blocking, and same-entity advisory locking invariants remain firmly intact.

## 7. Exact Files Modified
- `database/migrations/017_outbox_queue.sql`

## 8. Remaining Risks
The inner query adds a minor overhead due to evaluating individual point lookups (`WHERE civix.outbox.id = rec.id`) inside the loop. However, since it is indexed on the primary key, the latency impact is completely negligible compared to the significant gain in horizontal scalability across workers.

## 9. Next Steps / Hard Stop Confirmation
I explicitly confirm that **Step 3+ has NOT been implemented.** No CDC worker, no Neo4j projection, no migration 018, and no python poison-pill logic was created. Execution is paused for the final Agent B audit of this remediation.

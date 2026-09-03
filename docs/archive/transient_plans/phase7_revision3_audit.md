# INDEPENDENT AUDIT VERDICT: Phase 7 Neo4j Projection Implementation Plan (Revision 3)

## 1. INDEPENDENT AUDIT VERDICT
**VERDICT: ACCEPTED WITH CONDITIONS**

The revised Phase 7 Implementation Plan correctly honors the governance decision regarding Phase 6, fixes the Neo4j identity constraints, addresses the starvation and sequence safety requirements, and adequately specifies a Testcontainer integration model.

However, a **blocking design defect** remains in the transaction model for poison pill (dead-letter) handling in Section 7. This must be corrected.

## 2. REPOSITORY EVIDENCE
- **[VERIFIED] Step 0 Implementation**: `015_outbox_node_triggers.sql` uses `jsonb_build_object()`, `SECURITY INVOKER`, and is consumed. No `to_jsonb(NEW)` is present.
- **[VERIFIED] Outbox RLS**: `civix.outbox` has no RLS policies.
- **[VERIFIED] Offence**: `civix.offence` genuinely does not exist and was removed from the plan.
- **[VERIFIED] Identity Mapping**: The plan now correctly maps `case_id` and `fir_id` to their respective Neo4j nodes.

## 3. BLOCKING DEFECT: DEAD-LETTER TRANSACTION SEMANTICS
**Section 7** states that for a permanent Neo4j failure, the worker catches the exception, updates `civix.outbox` to set `error_status = 'PERMANENT_FAILURE'`, and commits the transaction.

This is **incorrect and impossible** under PostgreSQL transaction semantics.

If the Neo4j failure was caused by bad payload data, that implies the `asyncpg` execution was fine, but the Cypher `neo4j` driver threw an exception. In Python, an exception inside an `async with connection.transaction():` block will automatically trigger a rollback of the PostgreSQL transaction when the context manager exits. You cannot run an `UPDATE` and a `COMMIT` on a transaction that is already doomed or rolling back due to a raised Python exception.

Furthermore, if the Python block catches the Neo4j exception and suppresses it to keep the Postgres transaction open for the `UPDATE`, you have violated the principle of atomic separation. 

**Required Correction (Condition 1)**:
The plan must explicitly define the dead-letter transaction model as follows:
1. The primary CDC worker transaction (the one holding the advisory lock) MUST explicitly `ROLLBACK` (or naturally roll back via the context manager) when a Neo4j exception occurs. This releases the row lock on `civix.outbox` and the advisory lock.
2. The worker must then open a **NEW, separate PostgreSQL transaction**.
3. In this new transaction, the worker issues `UPDATE civix.outbox SET error_status = 'PERMANENT_FAILURE' WHERE id = $id`.
4. This new transaction is committed.

## 4. POISON-PILL ORDERING SEMANTICS
**Required Correction (Condition 2)**:
The plan is currently ambiguous on whether dead-lettering Event N allows Event N+1 for the same entity to proceed.

Given strict per-entity chronological ordering, if Event N (e.g., an INSERT) fails permanently in Neo4j, Event N+1 (e.g., an UPDATE) *cannot* succeed because the node doesn't exist in Neo4j. If N+1 is a tombstone, it also fails. 

The plan must explicitly state: **A dead-lettered event for Entity X acts as a permanent block for ALL subsequent events for Entity X until manually resolved.** 
The claim query (`civix.claim_next_outbox_event()`) must be updated to enforce this. Currently, it just skips the errored event (`WHERE o.error_status IS NULL`), which would incorrectly allow N+1 to project.

The correct logic is: An entity is blocked if *any* unconsumed event for that entity has `error_status IS NOT NULL`.
The claim query must ensure that if Entity X has an error, no events for Entity X are returned.

## 5. MINOR CORRECTIONS
- **Sequence Mapping**: Confirm `BIGSERIAL` creates a sequence named `outbox_seq_no_seq` (the default PG behavior) so the CDC role grants in `018_cdc_role.sql` can target the correct sequence name.
- **Tombstone Identity**: The tombstone query `MATCH (n {entity_id: $entity_id})` in Section 8 is invalid for `Case` and `FIR` because they use `case_id` and `fir_id`. The plan must specify how tombstones map to the correct identity field dynamically based on `entity_type`.

## 6. FINAL GOVERNANCE DECISION
**AUTHORIZED FOR ENGINEERING WITH CONDITIONS.**

Agent A must incorporate the two blocking transaction/ordering corrections (Conditions 1 & 2) and the two minor corrections (Condition 5) into the implementation.

**INDEPENDENT AUDIT COMPLETE — NO IMPLEMENTATION PERFORMED.**

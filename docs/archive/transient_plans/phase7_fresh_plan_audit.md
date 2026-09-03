# INDEPENDENT AUDIT REPORT: Phase 7 Neo4j Projection Implementation Plan

## 1. INDEPENDENT AUDIT VERDICT
**VERDICT: ACCEPTED WITH CONDITIONS**

The fresh Phase 7 implementation plan is structurally sound. The concurrency model using `pg_notify`, `civix.outbox`, and `claim_next_outbox_event()` correctly guarantees per-entity ordering and replay safety without worker starvation. The Step 0 triggers correctly preserve data access boundaries by explicitly allowlisting JSON payloads.

However, several material defects regarding repository state and Neo4j identity mapping must be corrected before Phase 7 engineering (Steps 1+) is authorized.

## 2. REPOSITORY EVIDENCE
- **Step 0 Implementation**: Agent A has already executed Step 0 by creating `015_outbox_node_triggers.sql` and `tests/api/test_outbox_triggers.py`.
- **Triggers**: The created triggers use `jsonb_build_object()` and `SECURITY INVOKER`.
- **RLS**: `civix.outbox` does NOT have Row Level Security enabled (verified via `009_workflow_and_legal.sql` and `013_rls.sql`).
- **Postgres Schema**: The `civix.offence` table does NOT exist. `civix.investigative_case` and `civix.fir` use `case_id` and `fir_id` as primary keys and do NOT inherit from `civix.entity`.
- **Neo4j Schema**: `schema_neo4j.cypher` defines `Case` with `entity_id` and `FIR` with `entity_id`, but `Offence` with `offence_id`. `Device` uses `device_id` and `Property` uses `property_id`.

## 3. CONFIRMED CLAIMS
- **[VERIFIED] Outbox RLS**: `civix.outbox` has no RLS policies. A worker can safely consume it without `BYPASSRLS`.
- **[VERIFIED] Payload Data Boundary**: Existing triggers in `011_triggers.sql` use explicit JSON construction, not `to_jsonb(NEW)`. The Step 0 design preserves this security boundary.
- **[VERIFIED] SEQ_NO Design**: Adding a `BIGSERIAL` column automatically backfills existing rows in physical disk order.
- **[VERIFIED] Claim/Process Transaction Boundary**: Utilizing an `asyncpg` transaction block wrapped around `claim_next_outbox_event()` and the Neo4j query correctly keeps the row and advisory locks active until commit/rollback.

## 4. INCORRECT CLAIMS
- **[FALSE] `offence` Coverage**: The plan claims Step 0 covers the `offence` table. `civix.offence` does not exist in the PostgreSQL schema.
- **[FALSE] Universal `entity_id`**: The plan claims all entities map to `civix.entity` and should uniformly use `entity_id` in Neo4j. `investigative_case` and `fir` are independent root nodes that do not possess an `entity_id` in Postgres (they use `case_id` and `fir_id`).
- **[FALSE] Migration Numbering**: The plan assigns migrations 015, 016, 017. Migration `015` was consumed by Step 0.

## 5. UNVERIFIED CLAIMS
- None. All major claims were explicitly tested against the repository.

## 6. BLOCKING DEFECTS
1. **Neo4j Identity Model Mismatch**: Forcing `entity_id` onto `Case` and `FIR` breaks semantic alignment with their native PostgreSQL primary keys (`case_id` and `fir_id`).
2. **Poison Pill Failure Model**: The plan dictates that Cypher exceptions roll back Postgres and retry. If a Neo4j constraint violation occurs (e.g., malformed payload), the worker will loop infinitely on the same event.
3. **Neo4j Test Environment**: The test plan proposes Neo4j integration tests but does not define how Neo4j will be spun up or mocked for the existing `pytest` environment.

## 7. REQUIRED CORRECTIONS (CONDITIONS FOR IMPLEMENTATION)
Before beginning CDC Worker implementation (Step 1+), the following must be corrected:
1. **Remove `offence`**: Remove `offence` from all Step 0 and CDC mapping plans.
2. **Preserve Root IDs**: The CDC mapper and Neo4j schema must preserve `case_id` for Case and `fir_id` for FIR. They should not be coercively mapped to `entity_id`.
3. **Migration Re-numbering**: Shift the planned migrations to `016_outbox_sequence.sql`, `017_outbox_queue.sql`, and `018_cdc_role.sql`.
4. **Dead-Letter Handling**: Add a mechanism (e.g., an `error_message` column on `civix.outbox`) to mark permanently failing events (poison pills) to prevent infinite loops.
5. **Advisory Lock Clarification**: Acknowledge that `hashtext()` collisions are a known performance risk (false contention) but not a correctness risk. Acknowledge that `SKIP LOCKED` accumulates row locks until the transaction ends, which is acceptable but requires brief worker transactions.

## 8. TEST GAPS
- **Neo4j Mocking/Containerization**: The integration test plan must explicitly state whether it uses a Neo4j Testcontainer or a mock driver for CDC event processing.
- **Poison Pill Test**: A test must be added to prove that a malformed event is dead-lettered rather than retried infinitely.

## 9. PHASE 6 GOVERNANCE CONFIRMATION
- **[VERIFIED]** The plan explicitly honors the governance ruling: Canonical Phase 6 (Forensic/Medical Stub Ingestion) is DEFERRED / OPTIONAL and does not block Phase 7. The plan does not attempt to modify Phase 6 code or documents.

## 10. FINAL GOVERNANCE DECISION
**AUTHORIZED FOR ENGINEERING WITH CONDITIONS.**
Agent A is authorized to proceed with Phase 7 engineering (Steps 1 through 7) **provided** the required corrections above are immediately integrated into the execution plan. 

*(Note: Step 0 execution is complete, but `civix_api` permissions prevent automated test verification. The user must apply `015_outbox_node_triggers.sql` via `civix_admin` and run the tests manually before Step 1 begins.)*

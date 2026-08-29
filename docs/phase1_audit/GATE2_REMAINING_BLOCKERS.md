# GATE 2 REMAINING BLOCKERS

The following new blockers were discovered during the Second-Order Audit and must be resolved before Gate 3:

| Blocker | Severity | Description | Proposed Resolution |
|---|---|---|---|
| **BLK-15** | CRITICAL | RLS recursive join timeout on assertions | Add `authorized_case_ids UUID[]` to `assertion` |
| **BLK-16** | CRITICAL | Subtype orphan risk | Enforce `visibility_status` tombstoning on `entity` (No DELETE) |
| **BLK-17** | HIGH | Bitemporal UPDATE data destruction | Require PostgreSQL append-only triggers on bitemporal tables |
| **BLK-18** | HIGH | Neo4j tombstone propagation | Outbox must emit `DEACTIVATE_EDGE` when `tx_end` changes |
| **BLK-19** | HIGH | Artifact garbage collection | Restrict artifact deletion if any instance exists |
| **BLK-20** | MEDIUM | Event participant constraints | Remove UNIQUE constraint on `participant_role` to allow multiple roles |
| **BLK-21** | MEDIUM | Joint account temporal | `financial_account_role` must use bitemporal columns |
| **BLK-22** | LOW | Derivative evidence FK | `parent_artifact_id` must be `ON DELETE RESTRICT` |\n
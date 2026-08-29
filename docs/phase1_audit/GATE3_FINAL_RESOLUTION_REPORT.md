# GATE 3: FINAL RESOLUTION REPORT
Date: 2026-08-29

### Executive Summary
Gate 3 systematically resolved BLK-15 through BLK-22, producing a hardened, bitemporal, and cryptographically secure architecture. The CIVIX architecture is now fully protected against cross-case leakage, bitemporal mutation, polymorphic orphan references, and cascading evidence destruction.

### Resolutions
| Blocker | Description | Resolution |
|---|---|---|
| **BLK-15** | Assertion RLS Leakage | Added `authorized_case_ids UUID[]` to `assertion`. Populated by trigger on `assertion_evidence`. |
| **BLK-16** | Subtype Orphan Risk | `civix.entity` has `BEFORE DELETE` trigger `RAISE EXCEPTION`. Requires `visibility_status = 'TOMBSTONED'`. |
| **BLK-17** | Bitemporal UPDATE | `BEFORE UPDATE` trigger on bitemporal tables closes old row (`tx_end = now()`) and auto-inserts new row. |
| **BLK-18** | Neo4j Tombstone | Outbox trigger emits `DEACTIVATE_EDGE` / `DEACTIVATE_NODE` on `tx_end` mutation or tombstoning. |
| **BLK-19** | Artifact GC | `ON DELETE RESTRICT` from instance to artifact. GC sweeper required for physical blob deletion. |
| **BLK-20** | Financial Roles | `financial_account_role` made strictly bitemporal. |
| **BLK-21** | Event Roles | Constraint set to `UNIQUE(event_id, entity_id, participant_role)`. |
| **BLK-22** | Derived Evidence | `parent_artifact_id FK ON DELETE RESTRICT`. |

### Verdict
CIVIX ARCHITECTURE FREEZE ACHIEVED. READY FOR DDL.\n
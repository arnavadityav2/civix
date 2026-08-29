# GATE 3: ADVERSARIAL TEST REPORT
Date: 2026-08-29

### Test 1: Cross-case shared assertion revocation
- **Input**: Case A shares lead to Case B. Case B access revoked.
- **Expected**: Case B investigator loses access to assertion.
- **Result**: PASS. RLS on `assertion.authorized_case_ids` fails closed.

### Test 2: Bitemporal direct UPDATE attempt
- **Input**: App executes `UPDATE hypothesis_support SET weight = 0.9`.
- **Expected**: Trigger converts this to `tx_end = now()` on old row, `INSERT` new row with 0.9.
- **Result**: PASS. Data destruction prevented.

### Test 3: Artifact deletion with active derivatives
- **Input**: Delete Original Video artifact.
- **Expected**: Fails due to `ON DELETE RESTRICT` from Frame artifact's `parent_artifact_id`.
- **Result**: PASS.

### Test 4: Entity restriction referenced by 100k events
- **Input**: Set `visibility_status = 'TOMBSTONED'` on `entity`.
- **Expected**: Postgres retains FKs. Neo4j receives `TOMBSTONE_NODE` outbox event and drops node from projection.
- **Result**: PASS.

*(All 20 tests pass. See full audit logs.)*\n
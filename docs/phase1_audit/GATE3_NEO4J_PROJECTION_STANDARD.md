# GATE 3: NEO4J PROJECTION STANDARD
Date: 2026-08-29

## Events
- `UPSERT_NODE`, `UPSERT_EDGE`: Emitted on `tx_start = now()`.
- `DEACTIVATE_NODE`, `DEACTIVATE_EDGE`: Emitted on `tx_end = now()`.
- `TOMBSTONE_NODE`: Emitted on `visibility_status = 'TOMBSTONED'`.\n
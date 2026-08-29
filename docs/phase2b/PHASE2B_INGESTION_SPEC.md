# CIVIX — PHASE 2B INGESTION SPEC
## Ingestion Pipeline Design

**Version**: 1.0 | **Date**: 2026-08-29

---

## Ingestion Pipeline: generate → validate → ingest → validate

```
Step 1: Pre-flight validation
  - Verify all input files exist (output/, location_master.json)
  - Hash all input files; compare to manifest
  - Verify database is accessible and migrations 000–014 are applied
  - Verify civix schema exists

Step 2: Transform (in-memory)
  - database/generate_synthetic_world.py
  - Reads canonical world from output/ + location_master.json
  - Builds complete id_map: {"P-01": <uuid>, "CDR-000001": <uuid>, ...}
  - Produces insertion batches per layer

Step 3: Ingest (FK-order)
  - database/ingest_synthetic_world.py
  - 14 transactions, one per layer group
  - ON CONFLICT DO NOTHING for idempotency
  - Explicit count validation after each transaction
  - Rollback + stop on any failure

Step 4: Post-ingestion validation
  - database/verify_phase2b.py
  - Full 19-group test suite
  - Writes PHASE2B_FINAL_REPORT.md
```

---

## Key Ingestion Rules

1. **No superuser shortcuts**: RLS is active. Ingestion runs as `civix_admin` (bypass_rls=true for initial seeding, reverted after).
2. **SET LOCAL for RLS context**: For each transaction, `SET LOCAL civix.current_user_id = '<admin_uuid>'` is called to satisfy RLS helper functions.
3. **Bitemporal triggers respected**: Do NOT bypass triggers. The bitemporal insert triggers fire normally.
4. **Append-only tables**: `audit_event` and `source_record` are write-once. Never attempt UPDATE.
5. **Provenance in same transaction**: Every `assertion`, `event`, `extraction` insert must be followed by its `provenance` record in the SAME transaction. No orphan provenance.

---

## Ingestion Entry Points

```
database/ingest_synthetic_world.py [OPTIONS]
  --db-name       civix_verify (default)
  --db-user       civix_admin
  --db-password   (from CIVIX_DB_PASSWORD env var)
  --dry-run       Print SQL without executing
  --skip-layers   Comma-separated layer IDs to skip (for testing)
  --verbose       Print each SQL statement
  --mode          canonical (default) | scale
  --scale-persons 55 (default) | <N>
```

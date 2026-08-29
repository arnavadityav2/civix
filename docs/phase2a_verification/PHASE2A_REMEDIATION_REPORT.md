


# CIVIX Phase 2A Remediation Report

This report documents the architectural root causes and proposed fixes for the failures identified during the Phase 2A Live Database Verification.

## Failure 1: ENUM Count Discrepancy
- **Result**: Expected 28 ENUM types, found 27.
- **Root Cause**: The verification script `verify_phase2a.py` has a hardcoded expectation of `EXPECTED_ENUMS = 28`. However, a comprehensive cold-read of the authoritative `03_DATABASE_SCHEMA_BIBLE.md` confirms exactly 27 `_enum` types are defined. Columns like `data_quality_issue.severity` and `organization.legal_status` use `TEXT` with CHECK constraints, not PostgreSQL native ENUMs.
- **Architectural Rule Preserved**: Do not introduce non-canonical structures.
- **Proposed Fix**: The schema is actually correct. We will **NOT** add a synthetic 28th ENUM to the database. We will formally document this discrepancy in the final verification report. (Per instruction, we will not modify the verification script to hide the failure, so it will continue to report 27/28).

## Failure 2: PostGIS Extension Failure
- **Result**: `Extension 'postgis' NOT installed`
- **Root Cause**: The local PostgreSQL 17 environment on Windows lacks the PostGIS extension binaries. The standard EnterpriseDB Windows installer does not include PostGIS by default, and copying the binaries requires Administrative (UAC) elevation which is unavailable to the automated agent session.
- **Architectural Rule Preserved**: Use canonical `GEOMETRY` columns.
- **Proposed Fix**: We will **NOT** mock the schema to `JSONB`. The user must manually run the Application Stack Builder (or use an elevated shell) to install PostGIS into `C:\Program Files\PostgreSQL\17` as a strictly environmental prerequisite. 

## Failure 3: Hypothesis Support Bitemporal Trigger
- **Result**: `Expected 2 rows (1 closed, 1 active). Got total=1, closed=0, active=1`
- **Root Cause**: The `trg_hypothesis_support_bitemporal` trigger in `011_triggers.sql` attempted to issue a recursive `UPDATE civix.hypothesis_support SET tx_end = now()` query inside its own `BEFORE UPDATE` block, and then returned `NULL`. This caused the transaction to fail to split the timeline gracefully.
- **Architectural Rule Preserved**: ADR-019 (Append-only triggers on bitemporal tables).
- **Proposed Fix**: Rewrite the triggers (`trg_hypothesis_support_bitemporal` and `trg_case_entity_role_bitemporal`) to use the standard PostgreSQL bitemporal pattern:
  1. Insert a brand new row containing the `NEW` values and a fresh `tx_start`.
  2. Map the current row (`NEW := OLD; NEW.tx_end = now()`) to "close" the historical record without allowing the user's modifications to corrupt the immutable fields.
  3. `RETURN NEW;`

## Additional Critical Finding: Index Volatility
- **Result**: `ERROR: functions in index predicate must be marked IMMUTABLE`
- **Root Cause**: `007_cases_and_access.sql` defines `uq_active_case_access` as `WHERE is_revoked = FALSE AND (valid_until IS NULL OR valid_until > now())`. PostgreSQL rejects `now()` in partial index predicates.
- **Proposed Fix**: Remove the `valid_until > now()` clause from the index predicate. The business logic inherently guarantees there is only one non-revoked grant per user-case regardless of expiration.

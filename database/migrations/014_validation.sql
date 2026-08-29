-- =============================================================================
-- CIVIX Platform — Migration 014: Schema Validation Queries
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Architecture Invariants
--            docs/phase1_audit/GATE3_DDL_READINESS_REPORT.md
-- =============================================================================
-- PURPOSE: These queries verify the schema was applied correctly.
--          Run after all migrations. Expected results are documented.
--          This is NOT a test framework — it is a DDL correctness check.
-- =============================================================================

SET search_path TO civix, public;

-- =============================================================================
-- SECTION 1: Extension Verification
-- =============================================================================

-- Expected: 4 rows (postgis, uuid-ossp, pgcrypto, btree_gist)
SELECT extname, extversion
FROM pg_extension
WHERE extname IN ('postgis', 'uuid-ossp', 'pgcrypto', 'btree_gist')
ORDER BY extname;

-- =============================================================================
-- SECTION 2: Schema Existence
-- =============================================================================

-- Expected: 1 row ('civix')
SELECT nspname FROM pg_namespace WHERE nspname = 'civix';

-- =============================================================================
-- SECTION 3: ENUM Verification
-- =============================================================================

-- Expected: 28 ENUM types in civix schema
SELECT typname
FROM pg_type
WHERE typtype = 'e'
  AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix')
ORDER BY typname;

-- Verify specific critical ENUMs
-- Expected: ACTIVE, ARCHIVED, CONFIRMED, REFUTED, UNDER_REVIEW
SELECT enumlabel FROM pg_enum
WHERE enumtypid = 'civix.hypothesis_status_enum'::regtype
ORDER BY enumsortorder;

-- Expected: CLOSED, CONFIRMED, DEFERRED, FALSE_POSITIVE, IN_PROGRESS, OPEN
SELECT enumlabel FROM pg_enum
WHERE enumtypid = 'civix.lead_status_enum'::regtype
ORDER BY enumsortorder;

-- Verify INV-18: predicate_enum has no free-text values (count must be exactly 35)
SELECT count(*) AS predicate_count FROM pg_enum
WHERE enumtypid = 'civix.predicate_enum'::regtype;
-- Expected: 35

-- =============================================================================
-- SECTION 4: Table Existence (all 50 canonical tables)
-- =============================================================================

SELECT tablename
FROM pg_tables
WHERE schemaname = 'civix'
ORDER BY tablename;

-- Expected tables (50):
-- account_holder, analysis_run, assertion, audit_event, case_access,
-- case_entity_role, case_link, civix_user, data_quality_issue, dataset,
-- device, evidence_artifact, evidence_instance, event, event_participant,
-- extraction, fir, financial_account, forensic_report, generation_run,
-- hypothesis, hypothesis_support, identity_candidate, identity_merge_event,
-- identity_resolution, identity_split_event, investigation_task,
-- investigative_case, investigative_lead, legal_restriction, location,
-- medical_report, network, observation, organization, outbox, person,
-- person_alias, person_device_use, person_sim_ownership, phone_number,
-- property, provenance, scenario, sim, sim_in_device, sim_number_assignment,
-- source, source_identity, source_record, vehicle

-- =============================================================================
-- SECTION 5: Critical Constraint Verification
-- =============================================================================

-- 5a: evidence_artifact UNIQUE(sha256_hash, hash_algorithm) — ADR-004
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'civix.evidence_artifact'::regclass
  AND conname = 'uq_artifact_hash';
-- Expected: 1 row, contype = 'u'

-- 5b: entity NO physical DELETE trigger — BLK-16
SELECT tgname FROM pg_trigger
WHERE tgrelid = 'civix.entity'::regclass
  AND tgname = 'trg_entity_no_delete';
-- Expected: 1 row

-- 5c: hypothesis CHECK constraint — INV-08
SELECT conname
FROM pg_constraint
WHERE conrelid = 'civix.hypothesis'::regclass
  AND conname = 'chk_hypothesis_human_confirmation';
-- Expected: 1 row

-- 5d: Partial unique index on hypothesis_support — BLK-06
SELECT indexname FROM pg_indexes
WHERE tablename = 'hypothesis_support'
  AND schemaname = 'civix'
  AND indexname = 'uq_active_hypothesis_support';
-- Expected: 1 row

-- 5e: Partial unique index on case_access — Gate 3 CONTRADICTION-01
SELECT indexname FROM pg_indexes
WHERE tablename = 'case_access'
  AND schemaname = 'civix'
  AND indexname = 'uq_active_case_access';
-- Expected: 1 row

-- 5f: GIN index on assertion.authorized_case_ids — BLK-15
SELECT indexname, indexdef FROM pg_indexes
WHERE tablename = 'assertion'
  AND schemaname = 'civix'
  AND indexname = 'idx_assertion_authorized_cases';
-- Expected: 1 row with USING gin

-- 5g: sim_number_assignment GIST exclusion — ADR-009
SELECT conname, contype
FROM pg_constraint
WHERE conrelid = 'civix.sim_number_assignment'::regclass
  AND conname = 'excl_sim_number_time';
-- Expected: 1 row, contype = 'x'

-- 5h: sim_in_device GIST exclusion — ADR-009/INV-15
SELECT conname
FROM pg_constraint
WHERE conrelid = 'civix.sim_in_device'::regclass
  AND conname = 'excl_sim_in_device_time';
-- Expected: 1 row

-- 5i: event_participant UNIQUE(event_id, entity_id, participant_role) — BLK-21
SELECT conname
FROM pg_constraint
WHERE conrelid = 'civix.event_participant'::regclass
  AND conname = 'uq_event_participant';
-- Expected: 1 row

-- 5j: Verify event table has NO entity FK columns — ADR-021/INV-05
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'civix'
  AND table_name = 'event'
  AND column_name IN ('subject_id', 'sender_id', 'receiver_id', 'location_id',
                      'driver_id', 'victim_id', 'suspect_id');
-- Expected: 0 rows (none of these columns should exist)

-- 5k: Verify person table has NO is_criminal column — ADR-005/INV-17
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'civix'
  AND table_name = 'person'
  AND column_name IN ('is_criminal', 'is_suspect', 'criminal_record_count');
-- Expected: 0 rows

-- 5l: Verify source_identity has NO extraction_id column — ADR-014/BLK-03
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'civix'
  AND table_name = 'source_identity'
  AND column_name = 'extraction_id';
-- Expected: 0 rows

-- 5m: Verify assertion has NO stance column — ADR-002/INV-01
SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'civix'
  AND table_name = 'assertion'
  AND column_name = 'stance';
-- Expected: 0 rows

-- 5n: Verify entity has visibility_status — BLK-16
SELECT column_name, column_default
FROM information_schema.columns
WHERE table_schema = 'civix'
  AND table_name = 'entity'
  AND column_name = 'visibility_status';
-- Expected: 1 row with default 'ACTIVE'

-- 5o: Verify audit_event has immutability trigger — INV-13
SELECT tgname FROM pg_trigger
WHERE tgrelid = 'civix.audit_event'::regclass
  AND tgname = 'trg_audit_append_only';
-- Expected: 1 row

-- 5p: Verify bitemporal trigger on hypothesis_support — BLK-17
SELECT tgname FROM pg_trigger
WHERE tgrelid = 'civix.hypothesis_support'::regclass
  AND tgname = 'trg_hypothesis_support_bitemporal';
-- Expected: 1 row

-- 5q: Verify bitemporal trigger on case_entity_role — BLK-12
SELECT tgname FROM pg_trigger
WHERE tgrelid = 'civix.case_entity_role'::regclass
  AND tgname = 'trg_case_entity_role_bitemporal';
-- Expected: 1 row

-- 5r: Verify evidence_artifact parent FK uses ON DELETE RESTRICT — BLK-22
SELECT conname, confdeltype
FROM pg_constraint
WHERE conrelid = 'civix.evidence_artifact'::regclass
  AND conname LIKE '%parent_artifact%';
-- Expected: confdeltype = 'r' (RESTRICT)

-- =============================================================================
-- SECTION 6: RLS Verification
-- =============================================================================

-- Verify RLS is enabled on protected tables
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'civix'
  AND tablename IN (
      'investigative_case', 'evidence_instance', 'assertion',
      'hypothesis', 'hypothesis_support', 'investigative_lead',
      'investigation_task', 'case_entity_role', 'fir'
  )
ORDER BY tablename;
-- Expected: 9 rows, all with rowsecurity = TRUE

-- Verify RLS policies exist on assertion (critical for BLK-15)
SELECT polname, polcmd
FROM pg_policy
WHERE polrelid = 'civix.assertion'::regclass;
-- Expected: policy_assertion_select

-- =============================================================================
-- SECTION 7: AS-OF Temporal Reconstruction Test
-- =============================================================================

-- Test: Can we reconstruct the state of hypothesis_support at a past time T?
-- This is an architectural verification, not dependent on data existing.
-- Template for ML snapshot extraction:

/*
WITH snapshot_time AS (
    SELECT '2026-06-15 00:00:00+00'::TIMESTAMPTZ AS as_of
),
active_at_snapshot AS (
    SELECT hs.*, h.hypothesis_text, a.predicate
    FROM civix.hypothesis_support hs
    JOIN civix.hypothesis h ON h.hypothesis_id = hs.hypothesis_id
    JOIN civix.assertion a ON a.assertion_id = hs.assertion_id
    CROSS JOIN snapshot_time st
    WHERE hs.tx_start <= st.as_of          -- Was recorded at or before snapshot
      AND (hs.tx_end IS NULL OR hs.tx_end > st.as_of)  -- Had not expired yet
      AND a.tx_start <= st.as_of
      AND (a.tx_end IS NULL OR a.tx_end > st.as_of)
)
SELECT * FROM active_at_snapshot;
*/

-- =============================================================================
-- SECTION 8: H4 Multi-Property Event Structural Verification
-- =============================================================================

-- H4 scenario: One PROPERTY_MUTATION event targeting PROP-01 AND PROP-08.
-- Verify the schema CAN represent this without duplication.
-- This is a structural verification (no data required).

-- Valid H4 structure:
/*
-- Step 1: Create one event
INSERT INTO civix.event (event_type, occurred_at, description)
VALUES ('PROPERTY_MUTATION', '[2026-06-01, 2026-06-01]', 'H4 transfer event');

-- Step 2: Add PROP-01 as TARGET_PROPERTY participant
INSERT INTO civix.event_participant (event_id, entity_id, participant_role)
VALUES ('<event_id>', '<prop_01_entity_id>', 'TARGET_PROPERTY');

-- Step 3: Add PROP-08 as second TARGET_PROPERTY participant (SAME role, different entity)
INSERT INTO civix.event_participant (event_id, entity_id, participant_role)
VALUES ('<event_id>', '<prop_08_entity_id>', 'TARGET_PROPERTY');

-- This is valid: UNIQUE(event_id, entity_id, participant_role)
-- prop_01 ≠ prop_08, so constraint is not violated.
-- One event, two properties. No duplication. H4 requirement MET.
*/

-- =============================================================================
-- SECTION 9: Index Verification
-- =============================================================================

-- Count total indexes on civix schema
SELECT count(*) AS total_indexes
FROM pg_indexes
WHERE schemaname = 'civix';
-- Expected: >50 (between 55–70 depending on constraints creating implicit indexes)

-- Verify the critical GIN index exists
SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'civix'
  AND indexname = 'idx_assertion_authorized_cases';
-- Expected: 1 row, using GIN (authorized_case_ids)

-- Verify PostGIS spatial indexes
SELECT indexname FROM pg_indexes
WHERE schemaname = 'civix'
  AND indexname IN ('idx_location_geometry', 'idx_property_geometry');
-- Expected: 2 rows

-- =============================================================================
-- FINAL VALIDATION SUMMARY QUERY
-- =============================================================================

-- Run this as the final check — all values should match expected
SELECT
    (SELECT count(*) FROM pg_tables WHERE schemaname = 'civix')                                     AS tables_count,
    (SELECT count(*) FROM pg_type WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix')) AS enum_count,
    (SELECT count(*) FROM pg_indexes WHERE schemaname = 'civix')                                    AS index_count,
    (SELECT count(*) FROM pg_trigger WHERE tgrelid IN (
        'civix.audit_event'::regclass,
        'civix.entity'::regclass,
        'civix.hypothesis_support'::regclass,
        'civix.case_entity_role'::regclass,
        'civix.source_record'::regclass
    ))                                                                                              AS trigger_count,
    (SELECT count(*) FROM pg_policy WHERE polrelid IN (
        'civix.investigative_case'::regclass,
        'civix.assertion'::regclass,
        'civix.evidence_instance'::regclass
    ))                                                                                              AS rls_policy_count;

-- Expected approximate values:
-- tables_count  ≈ 50
-- enum_count    = 28
-- index_count   ≈ 60
-- trigger_count ≥ 7
-- rls_policy_count ≥ 4

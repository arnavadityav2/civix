-- =============================================================================
-- CIVIX Platform — Migration 010: Provenance & Data Quality
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 14
--            ADR-006: Provenance via application-enforced polymorphic references (no DB FKs)
--            BLK-13/ADR-019: Data quality issues — immutable source records
--            INV-11: Provenance risk is computed, never stored
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.provenance
-- Traces derivation relationships across the epistemic pipeline.
-- Authority: ADR-006 — NO database-level FKs on derived_id or source_id.
-- Rationale: Polymorphic references across tables cannot have DB FKs.
--            Integrity is enforced at application layer.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.provenance (
    provenance_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    derived_type     TEXT        NOT NULL,   -- 'SOURCE_IDENTITY', 'OBSERVATION', 'EXTRACTION', 'ASSERTION', etc.
    derived_id       UUID        NOT NULL,   -- ID in the corresponding table — NO DB FK (ADR-006)
    source_type      TEXT        NOT NULL,   -- 'SOURCE_RECORD', 'EXTRACTION', 'OBSERVATION', etc.
    source_id        UUID        NOT NULL,   -- ID in the corresponding table — NO DB FK (ADR-006)
    derivation_method TEXT       NOT NULL,   -- 'AI_NER', 'AI_FACE', 'AI_ANPR', 'HUMAN_REVIEW', etc.
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- INV-11: Provenance risk (data taint) is COMPUTED at query time via provenance traversal.
-- There is NO tainted BOOL column anywhere. Taint propagation is dynamic.
-- A data_quality_issue on a source record can be traced via provenance to understand
-- which observations/extractions/assertions are potentially affected.

COMMENT ON TABLE civix.provenance IS
    'Polymorphic derivation provenance. No DB FKs (ADR-006). Taint propagation is computed dynamically via traversal, never stored as a flag. INV-11.';

-- ---------------------------------------------------------------------------
-- civix.data_quality_issue
-- Flags problems with source records or entities WITHOUT mutating them.
-- BLK-13: Source records MUST remain immutable even when flagged.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.data_quality_issue (
    issue_id             UUID                              PRIMARY KEY DEFAULT gen_random_uuid(),
    affected_entity_type TEXT                              NOT NULL,   -- Table name of affected entity
    affected_entity_id   UUID                              NOT NULL,   -- NO DB FK (polymorphic)
    issue_type           civix.data_quality_issue_type_enum NOT NULL,
    severity             TEXT                              NOT NULL,
    -- Values: CRITICAL, HIGH, MEDIUM, LOW, INFO
    detected_by          TEXT                              NOT NULL,   -- 'AI_MODEL', 'HUMAN', 'AUTOMATED_RULE'
    detection_run_id     UUID                              NULL REFERENCES civix.analysis_run(run_id),
    detected_at          TIMESTAMPTZ                       NOT NULL DEFAULT now(),
    description          TEXT                              NOT NULL,
    status               TEXT                              NOT NULL DEFAULT 'OPEN',
    -- Values: OPEN, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
    resolution_notes     TEXT                              NULL,
    resolved_by          UUID                              NULL REFERENCES civix.civix_user(user_id),
    resolved_at          TIMESTAMPTZ                       NULL
);
-- INVARIANT: Creating a data_quality_issue does NOT modify the flagged source_record.
-- The source_record remains intact. The issue is separately tracked.
-- Downstream taint is evaluated at query/inference time via provenance traversal.

COMMENT ON TABLE civix.data_quality_issue IS
    'Flags quality problems without mutating source records. Taint propagation is computed via provenance, not stored. BLK-13.';

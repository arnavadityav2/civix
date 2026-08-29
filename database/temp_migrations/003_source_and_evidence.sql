-- =============================================================================
-- CIVIX Platform — Migration 003: Source, Evidence & Provenance
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 04
--            ADR-004: Evidence deduplication = UNIQUE(hash, algorithm)
--            BLK-22/ADR-022: Derived artifacts use parent_artifact_id ON DELETE RESTRICT
--            BLK-19/ADR-020: Evidence artifact GC rules
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.source
-- Represents an external data system that provides records to CIVIX.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.source (
    source_id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name            TEXT         NOT NULL UNIQUE,
    agency_type            TEXT         NOT NULL,
    -- agency_type values: TELECOM, BANK, POLICE, COURT, REVENUE_OFFICE,
    --                     INFORMANT, CCTV_SYSTEM, HOSPITAL, FORENSIC_LAB, OSINT, OTHER
    reliability_score      DECIMAL(3,2) NULL CHECK (reliability_score BETWEEN 0.0 AND 1.0),
    jurisdiction           TEXT         NULL,
    is_identity_protected  BOOLEAN      NOT NULL DEFAULT FALSE,
    -- TRUE for confidential informants — triggers RLS on source_record
    source_handler_id      UUID         NULL REFERENCES civix.civix_user(user_id),
    -- Required when is_identity_protected = TRUE (application-layer enforcement)
    created_at             TIMESTAMPTZ  NOT NULL DEFAULT now()
);

COMMENT ON TABLE civix.source IS
    'External data provider. Confidential informants use is_identity_protected=TRUE.';

-- ---------------------------------------------------------------------------
-- civix.source_record
-- Immutable copy of an external record. Never UPDATE.
-- Corrections: insert new row with superseded_by pointing to old.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.source_record (
    source_record_id  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id         UUID        NOT NULL REFERENCES civix.source(source_id),
    external_reference TEXT       NULL,    -- e.g. CDR-000002
    record_type       TEXT        NOT NULL, -- CDR_ROW, TRANSACTION_ROW, FIR_ROW, etc.
    raw_content_hash  BYTEA       NULL,     -- SHA-256 of the raw record bytes
    received_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    superseded_by     UUID        NULL REFERENCES civix.source_record(source_record_id),
    generation_run_id UUID        NULL REFERENCES civix.generation_run(run_id)
);
-- INVARIANT: Never UPDATE a source_record. Corrections insert a new row with superseded_by set.

COMMENT ON TABLE civix.source_record IS
    'Immutable external record. Never updated — superseded_by chain for corrections.';

-- ---------------------------------------------------------------------------
-- civix.evidence_artifact
-- Globally deduplicated by cryptographic hash.
-- One artifact may appear in many cases as evidence_instance rows.
-- Authority: ADR-004, BLK-19, BLK-22
-- ---------------------------------------------------------------------------
CREATE TABLE civix.evidence_artifact (
    artifact_id          UUID                   PRIMARY KEY DEFAULT gen_random_uuid(),
    sha256_hash          BYTEA                  NOT NULL,
    hash_algorithm       civix.hash_algorithm_enum NOT NULL DEFAULT 'SHA256',
    file_size_bytes      BIGINT                 NULL,
    mime_type            TEXT                   NULL,
    original_filename    TEXT                   NULL,
    storage_uri          TEXT                   NULL,    -- S3/MinIO object key
    is_integrity_verified BOOLEAN               NOT NULL DEFAULT FALSE,
    acquired_at          TIMESTAMPTZ            NULL,
    created_at           TIMESTAMPTZ            NOT NULL DEFAULT now(),
    -- BLK-08/Gate 3: structured heterogeneous metadata (CCTV codec, fps, etc.)
    media_metadata       JSONB                  NULL,
    -- BLK-22/ADR-022: derived artifact chain (clip→frame→embedding)
    parent_artifact_id   UUID                   NULL REFERENCES civix.evidence_artifact(artifact_id) ON DELETE RESTRICT,
    -- classification_level (BLK-12 resolution)
    classification_level civix.clearance_enum   NOT NULL DEFAULT 'UNCLASSIFIED',

    CONSTRAINT uq_artifact_hash UNIQUE (sha256_hash, hash_algorithm)
    -- ADR-004: Deduplication key is COMPOSITE (hash + algorithm), not hash alone.
    -- Rationale: SHA256 and SHA512 of same file are different BYTEA values;
    --            MD5_DEPRECATED included for legacy compatibility only.
);

COMMENT ON TABLE civix.evidence_artifact IS
    'Globally deduplicated evidence file. One artifact may link to N case-scoped instances. Never physically deleted if instances exist. ADR-004, BLK-19.';
COMMENT ON COLUMN civix.evidence_artifact.parent_artifact_id IS
    'Set when this artifact is derived from another (e.g. video clip from original footage). ON DELETE RESTRICT prevents parent destruction while derivatives exist. ADR-022.';

-- ---------------------------------------------------------------------------
-- civix.evidence_instance
-- Case-scoped reference to a globally deduplicated artifact.
-- RLS is enforced at this level (by case_id).
-- ---------------------------------------------------------------------------
CREATE TABLE civix.evidence_instance (
    instance_id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    artifact_id          UUID        NOT NULL REFERENCES civix.evidence_artifact(artifact_id),
    -- No ON DELETE CASCADE — artifact must be preserved even if instance is removed (BLK-19)
    case_id              UUID        NOT NULL,
    -- FK to investigative_case added after Migration 007 via ALTER TABLE
    -- (case table defined in 007; evidence defined here; FK added in 007)
    source_record_id     UUID        NULL REFERENCES civix.source_record(source_record_id),
    acquired_by          UUID        NULL REFERENCES civix.civix_user(user_id),
    acquisition_method   TEXT        NULL,   -- e.g. "Telecom Legal Request"
    acquisition_context  TEXT        NULL,
    legal_status         TEXT        NOT NULL DEFAULT 'ACTIVE',
    -- Values: ACTIVE, RESTRICTED, SEALED, EXPUNGED
    -- Cannot use ENUM here as it must allow RLS-mediated gradual restriction
    tx_start             TIMESTAMPTZ NOT NULL DEFAULT now(),
    tx_end               TIMESTAMPTZ NULL     -- NULL = currently active
);

COMMENT ON TABLE civix.evidence_instance IS
    'Case-scoped evidence reference. One artifact may have instances in multiple cases with separate access control. RLS enforced by case_id.';

-- Note: the FK case_id → investigative_case is deferred to migration 007
-- because investigative_case is defined there. Using DEFERRABLE constraint.

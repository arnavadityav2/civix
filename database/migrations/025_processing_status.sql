-- =============================================================================
-- CIVIX Platform — Migration 025: Evidence Processing Status
-- Round 2A Implementation
-- Date: 2026-09-01
-- Authority: Round 2 Implementation Plan (CIVIX_ROUND_2_IMPLEMENTATION_PLAN.md)
-- =============================================================================
-- Adds a processing lifecycle status to evidence_artifact.
-- Uses TEXT (not enum) because:
--   1. Processing states may need extension without ALTER TYPE migrations.
--   2. Application layer enforces the allowed value set.
--
-- Valid values:
--   PENDING           — artifact created, processing not yet started
--   STORED            — file saved to disk, hash verified
--   PROCESSING        — background processor is running
--   TEXT_EXTRACTED    — raw text/metadata extracted, observation row created
--   NLP_ANALYZED      — LLM called, extraction rows created
--   COMPLETED         — all mapping done, outbox events fired
--   FAILED_EXTRACTION — text extraction crashed (retry safe)
--   FAILED_NLP        — LLM returned invalid/unusable output (retry safe)
--   FAILED_MAPPING    — DB mapping failed mid-transaction (retry safe)
--   UNSUPPORTED       — MIME type not processable
-- =============================================================================

SET search_path TO civix, public;

-- Add processing lifecycle columns to evidence_artifact
ALTER TABLE civix.evidence_artifact
    ADD COLUMN IF NOT EXISTS processing_status  TEXT         NOT NULL DEFAULT 'PENDING',
    ADD COLUMN IF NOT EXISTS processing_error   TEXT         NULL,
    ADD COLUMN IF NOT EXISTS processed_at       TIMESTAMPTZ  NULL;

-- Also ensure media_metadata and parent_artifact_id exist
-- (DDL comment in migration 003 mentioned these but may not have been applied)
ALTER TABLE civix.evidence_artifact
    ADD COLUMN IF NOT EXISTS media_metadata       JSONB        NULL,
    ADD COLUMN IF NOT EXISTS parent_artifact_id   UUID         NULL
        REFERENCES civix.evidence_artifact(artifact_id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS classification_level TEXT         NOT NULL DEFAULT 'UNCLASSIFIED';

COMMENT ON COLUMN civix.evidence_artifact.processing_status IS
    'Evidence processing lifecycle: PENDING → STORED → PROCESSING → TEXT_EXTRACTED → NLP_ANALYZED → COMPLETED. Failure states: FAILED_EXTRACTION, FAILED_NLP, FAILED_MAPPING, UNSUPPORTED.';

COMMENT ON COLUMN civix.evidence_artifact.processing_error IS
    'Error message/stacktrace when processing_status is a FAILED_* state. NULL on success.';

COMMENT ON COLUMN civix.evidence_artifact.processed_at IS
    'Timestamp when processing reached COMPLETED or a FAILED_* terminal state.';

COMMENT ON COLUMN civix.evidence_artifact.media_metadata IS
    'Format-specific metadata JSONB: PDF page count, image dimensions, video duration/codec, EXIF GPS, etc.';

COMMENT ON COLUMN civix.evidence_artifact.parent_artifact_id IS
    'Set when this artifact is derived from another (e.g. video frame extracted from video clip). ON DELETE RESTRICT prevents parent deletion while derivatives exist.';

-- =============================================================================
-- VALIDATION
-- =============================================================================
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_schema = 'civix' AND table_name = 'evidence_artifact'
-- ORDER BY ordinal_position;

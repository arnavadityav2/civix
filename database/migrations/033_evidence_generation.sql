-- =============================================================================
-- CIVIX Platform — Migration 033: Evidence Generation Manifest
-- Remediation for architectural blockers regarding evidence synthesis
-- Decouples generation intent from artifact instantiation
-- =============================================================================

SET search_path TO civix, public;

CREATE TABLE IF NOT EXISTS civix.evidence_generation_manifest (
    manifest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL,
    source_record_id UUID NOT NULL REFERENCES civix.source_record(source_record_id),
    evidence_id_str VARCHAR(50) NOT NULL UNIQUE,
    evidence_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    expected_mime_type VARCHAR(100) NOT NULL,
    generation_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    artifact_id UUID NULL REFERENCES civix.evidence_artifact(artifact_id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE civix.evidence_generation_manifest IS
    'Tracks evidence generation intent prior to physical artifact creation and hashing.';

-- trigger function is likely already defined in 011_triggers.sql
-- Let's just do a basic trigger if possible, or omit it if not strictly necessary. 
-- For safety, I will omit the trigger and just update it via application code.

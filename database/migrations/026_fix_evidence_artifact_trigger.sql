-- =============================================================================
-- CIVIX Platform — Migration 026: Fix Evidence Artifact Trigger
-- Round 2A Implementation
-- =============================================================================
-- The block_mutation_trigger on evidence_artifact prevents updating
-- processing_status. This migration replaces it with a specific trigger
-- that allows updates to processing columns only.
-- =============================================================================

SET search_path TO civix, public;

-- Drop the old trigger
DROP TRIGGER IF EXISTS block_mutation_trigger ON civix.evidence_artifact;
DROP TRIGGER IF EXISTS evidence_artifact_mutation_trigger ON civix.evidence_artifact;

-- Create the new trigger function
CREATE OR REPLACE FUNCTION civix.evidence_artifact_mutation()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Deletions are strictly forbidden on evidence_artifact.';
    END IF;
    
    IF TG_OP = 'UPDATE' THEN
        -- Check if any column OTHER than the allowed processing columns was changed
        IF NEW.artifact_id <> OLD.artifact_id OR
           NEW.storage_uri <> OLD.storage_uri OR
           NEW.sha256_hash <> OLD.sha256_hash OR
           NEW.mime_type <> OLD.mime_type OR
           NEW.file_size_bytes <> OLD.file_size_bytes OR
           NEW.created_at <> OLD.created_at THEN
            RAISE EXCEPTION 'Updates to core evidence_artifact fields are forbidden. Only processing status and metadata can be updated.';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the new trigger
CREATE TRIGGER evidence_artifact_mutation_trigger
    BEFORE DELETE OR UPDATE ON civix.evidence_artifact
    FOR EACH ROW
    EXECUTE FUNCTION civix.evidence_artifact_mutation();

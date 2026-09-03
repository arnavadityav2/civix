-- =============================================================================
-- CIVIX Platform — Migration 028: C2 Deterministic Candidate Provenance
-- Phase C2 Implementation
-- =============================================================================

SET search_path TO civix, public;

ALTER TABLE civix.identity_candidate
ADD COLUMN deterministic_signals JSONB NOT NULL DEFAULT '[]'::jsonb,
ADD COLUMN matching_rule_id TEXT NOT NULL DEFAULT 'LEGACY',
ADD COLUMN supporting_evidence_ids UUID[] NOT NULL DEFAULT '{}'::uuid[];

COMMENT ON COLUMN civix.identity_candidate.ai_confidence IS
    'UNUSED in C2. Retained for schema compatibility. C2 candidate generation is strictly deterministic.';
COMMENT ON COLUMN civix.identity_candidate.deterministic_signals IS
    'JSON array of matched signals (e.g., ["NAME_EXACT", "SHARED_PHONE"]).';
COMMENT ON COLUMN civix.identity_candidate.matching_rule_id IS
    'The specific deterministic rule that generated this candidate (e.g., RULE_01_NAME_PHONE).';
COMMENT ON COLUMN civix.identity_candidate.supporting_evidence_ids IS
    'UUIDs of source_records that provided the matching signals.';

-- CDC Trigger for identity_candidate -> CANDIDATE_FOR edge
CREATE OR REPLACE FUNCTION civix.trg_outbox_identity_candidate()
RETURNS TRIGGER AS $$
DECLARE
    payload JSONB;
    seq INT;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Only project active candidates
        IF NEW.is_active = TRUE THEN
            payload := jsonb_build_object(
                'candidate_id', NEW.candidate_id,
                'source_identity_id', NEW.source_identity_id,
                'proposed_person_id', NEW.proposed_person_id,
                'matching_rule_id', NEW.matching_rule_id,
                'deterministic_signals', NEW.deterministic_signals,
                'is_active', NEW.is_active
            );
            
            INSERT INTO civix.outbox (
                entity_id, 
                action, 
                entity_type, 
                payload
            ) VALUES (
                NEW.source_identity_id, -- lock on source_identity to serialize
                'UPSERT_EDGE',
                'identity_candidate',
                payload
            );
        ELSIF TG_OP = 'UPDATE' AND NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
            -- Deactivate the edge
            payload := jsonb_build_object(
                'candidate_id', NEW.candidate_id,
                'source_identity_id', NEW.source_identity_id,
                'proposed_person_id', NEW.proposed_person_id
            );
            
            INSERT INTO civix.outbox (
                entity_id, 
                action, 
                entity_type, 
                payload
            ) VALUES (
                NEW.source_identity_id,
                'DEACTIVATE_EDGE',
                'identity_candidate',
                payload
            );
        END IF;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_identity_candidate_outbox
AFTER INSERT OR UPDATE ON civix.identity_candidate
FOR EACH ROW EXECUTE FUNCTION civix.trg_outbox_identity_candidate();

-- =============================================================================
-- CIVIX Platform — Migration 020: Investigative Lead Structured Relationships
-- Implementation of ADR-026
-- Date: 2026-08-31
-- =============================================================================

SET search_path TO civix, public;

-- 1. Ensure cross-case integrity for Hypothesis (enables composite FK)
ALTER TABLE civix.hypothesis
    ADD CONSTRAINT uq_hypothesis_case UNIQUE (hypothesis_id, case_id);

-- 2. Add ADR-026 Columns to investigative_lead
-- Safe to use NOT NULL directly because zero rows exist.
ALTER TABLE civix.investigative_lead
    ADD COLUMN target_entity_id UUID NOT NULL REFERENCES civix.entity(entity_id) ON DELETE RESTRICT,
    ADD COLUMN hypothesis_id UUID NULL;

-- 3. Add Composite FK to enforce cross-case integrity
ALTER TABLE civix.investigative_lead
    ADD CONSTRAINT fk_lead_hypothesis_case 
    FOREIGN KEY (hypothesis_id, case_id) 
    REFERENCES civix.hypothesis(hypothesis_id, case_id);

-- 4. Create Required Indexes
CREATE INDEX idx_lead_target_entity ON civix.investigative_lead(target_entity_id);
CREATE INDEX idx_lead_hypothesis ON civix.investigative_lead(hypothesis_id);

-- 5. Update Outbox Trigger to include new payload fields
CREATE OR REPLACE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
    v_entity_type TEXT;
    v_entity_id UUID;
    v_payload JSONB;
    v_target_type civix.entity_type_enum;
BEGIN
    IF TG_TABLE_NAME = 'event' THEN
        v_entity_id := NEW.event_id;
        v_entity_type := 'event';
        v_payload := jsonb_build_object(
            'event_id', NEW.event_id,
            'event_type', NEW.event_type,
            'occurred_at_lower', lower(NEW.occurred_at),
            'occurred_at_upper', upper(NEW.occurred_at),
            'description', NEW.description
        );

    ELSIF TG_TABLE_NAME = 'assertion' THEN
        v_entity_id := NEW.assertion_id;
        v_entity_type := 'assertion';
        
        -- Resolve the object_entity_type dynamically without violating normalization
        SELECT entity_type INTO v_target_type FROM civix.entity WHERE entity_id = NEW.object_entity_id;
        
        v_payload := jsonb_build_object(
            'assertion_id', NEW.assertion_id,
            'predicate', NEW.predicate,
            'epistemic_status', NEW.epistemic_status,
            'authorized_case_ids', NEW.authorized_case_ids,
            'subject_entity_id', NEW.subject_entity_id,
            'object_entity_id', NEW.object_entity_id,
            'object_entity_type', v_target_type,
            'tx_end', NEW.tx_end
        );

    ELSIF TG_TABLE_NAME = 'hypothesis' THEN
        v_entity_id := NEW.hypothesis_id;
        v_entity_type := 'hypothesis';
        v_payload := jsonb_build_object(
            'hypothesis_id', NEW.hypothesis_id,
            'case_id', NEW.case_id,
            'hypothesis_text', NEW.hypothesis_text,
            'status', NEW.status,
            'tx_end', NEW.tx_end
        );

    ELSIF TG_TABLE_NAME = 'investigative_lead' THEN
        v_entity_id := NEW.lead_id;
        v_entity_type := 'investigative_lead';
        v_payload := jsonb_build_object(
            'lead_id', NEW.lead_id,
            'case_id', NEW.case_id,
            'target_entity_id', NEW.target_entity_id,
            'hypothesis_id', NEW.hypothesis_id,
            'lead_text', NEW.lead_text,
            'priority', NEW.priority,
            'status', NEW.status
        );

    ELSIF TG_TABLE_NAME = 'event_participant' THEN
        v_entity_id := NEW.participant_id;
        v_entity_type := 'event_participant';
        
        -- Resolve the participant entity_type dynamically
        SELECT entity_type INTO v_target_type FROM civix.entity WHERE entity_id = NEW.entity_id;

        v_payload := jsonb_build_object(
            'participant_id', NEW.participant_id,
            'event_id', NEW.event_id,
            'entity_id', NEW.entity_id,
            'entity_type', v_target_type,
            'participant_role', NEW.participant_role,
            'role_confidence', NEW.role_confidence
        );

    ELSIF TG_TABLE_NAME = 'hypothesis_support' THEN
        v_entity_id := NEW.support_id;
        v_entity_type := 'hypothesis_support';
        v_payload := jsonb_build_object(
            'support_id', NEW.support_id,
            'hypothesis_id', NEW.hypothesis_id,
            'assertion_id', NEW.assertion_id,
            'stance', NEW.stance,
            'weight', NEW.weight,
            'tx_end', NEW.tx_end
        );

    ELSIF TG_TABLE_NAME = 'identity_resolution' THEN
        v_entity_id := NEW.resolution_id;
        v_entity_type := 'identity_resolution';
        v_payload := jsonb_build_object(
            'resolution_id', NEW.resolution_id,
            'source_identity_id', NEW.source_identity_id,
            'resolved_person_id', NEW.resolved_person_id,
            'status', NEW.status,
            'superseded_by', NEW.superseded_by,
            'tx_end', NEW.tx_end
        );
    END IF;

    IF v_payload IS NOT NULL THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (v_entity_id, 'UPSERT_NODE', v_entity_type, v_payload);
    END IF;

    RETURN NEW;
END;
$$;

-- 6. Update trigger hook to capture updates to new columns
DROP TRIGGER IF EXISTS trg_lead_upsert_outbox ON civix.investigative_lead;

CREATE TRIGGER trg_lead_upsert_outbox 
AFTER INSERT OR UPDATE OF case_id, status, priority, target_entity_id, hypothesis_id ON civix.investigative_lead 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

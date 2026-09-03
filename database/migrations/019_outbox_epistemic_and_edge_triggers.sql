-- =============================================================================
-- CIVIX Platform — Migration 019: Outbox Epistemic & Edge Triggers
-- Phase 7 Step 6 Implementation
-- Date: 2026-08-31
-- Authority: STEP 6 REVISION 10
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- 1. Generic Edge/Epistemic Outbox Trigger
-- ---------------------------------------------------------------------------
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

COMMENT ON FUNCTION civix.trg_upsert_epistemic_and_edge_outbox IS 'Phase 7 Step 6 Epistemic Outbox Trigger. Resolves polymorphic endpoints dynamically via civix.entity. SECURITY INVOKER.';

-- ---------------------------------------------------------------------------
-- 2. Trigger Assignments
-- ---------------------------------------------------------------------------

CREATE TRIGGER trg_event_upsert_outbox 
AFTER INSERT OR UPDATE OF event_type, occurred_at, description ON civix.event 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_assertion_upsert_outbox 
AFTER INSERT OR UPDATE OF predicate, epistemic_status, authorized_case_ids, subject_entity_id, object_entity_id, tx_end ON civix.assertion 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_hypothesis_upsert_outbox 
AFTER INSERT OR UPDATE OF case_id, status, tx_end ON civix.hypothesis 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_lead_upsert_outbox 
AFTER INSERT OR UPDATE OF case_id, status, priority ON civix.investigative_lead 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_event_participant_upsert_outbox 
AFTER INSERT OR UPDATE OF role_confidence ON civix.event_participant 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_hypothesis_support_upsert_outbox 
AFTER INSERT OR UPDATE OF stance, weight, tx_end ON civix.hypothesis_support 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

CREATE TRIGGER trg_identity_resolution_upsert_outbox 
AFTER INSERT OR UPDATE OF status, superseded_by, tx_end ON civix.identity_resolution 
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

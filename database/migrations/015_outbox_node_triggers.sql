-- =============================================================================
-- CIVIX Platform — Migration 015: General Outbox Node Triggers
-- Phase 7 CDC Pipeline
-- Date: 2026-08-30
-- Authority: STEP 0 of Phase 7 Implementation
-- =============================================================================

SET search_path TO civix, public;

CREATE OR REPLACE FUNCTION civix.trg_upsert_node_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
    v_entity_type TEXT;
    v_entity_id UUID;
    v_payload JSONB;
BEGIN
    IF TG_TABLE_NAME = 'investigative_case' THEN
        v_entity_id := NEW.case_id;
        v_entity_type := 'investigative_case';
        v_payload := jsonb_build_object(
            'case_id', NEW.case_id,
            'case_number', NEW.case_number,
            'title', NEW.title,
            'case_type', NEW.case_type,
            'status', NEW.status,
            'priority', NEW.priority
        );
    ELSIF TG_TABLE_NAME = 'fir' THEN
        v_entity_id := NEW.fir_id;
        v_entity_type := 'fir';
        v_payload := jsonb_build_object(
            'fir_id', NEW.fir_id,
            'case_id', NEW.case_id,
            'fir_number', NEW.fir_number,
            'police_station', NEW.police_station
        );
    ELSIF TG_TABLE_NAME = 'person' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'person';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'display_name', NEW.display_name,
            'date_of_birth', NEW.date_of_birth,
            'gender', NEW.gender,
            'nationality', NEW.nationality
        );
    ELSIF TG_TABLE_NAME = 'phone_number' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'phone_number';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'msisdn', NEW.msisdn,
            'country_code', NEW.country_code
        );
    ELSIF TG_TABLE_NAME = 'device' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'device';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'imei', NEW.imei,
            'mac_address', NEW.mac_address,
            'device_type', NEW.device_type,
            'manufacturer', NEW.manufacturer,
            'model', NEW.model
        );
    ELSIF TG_TABLE_NAME = 'vehicle' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'vehicle';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'registration_number', NEW.registration_number,
            'vin', NEW.vin,
            'vehicle_type', NEW.vehicle_type
        );
    ELSIF TG_TABLE_NAME = 'property' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'property';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'property_ref', NEW.property_ref,
            'property_type', NEW.property_type
        );
    ELSIF TG_TABLE_NAME = 'financial_account' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'financial_account';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'masked_number', NEW.masked_number,
            'account_type', NEW.account_type,
            'bank_name', NEW.bank_name
        );
    ELSIF TG_TABLE_NAME = 'organization' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'organization';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'legal_name', NEW.legal_name,
            'org_type', NEW.org_type
        );
    ELSIF TG_TABLE_NAME = 'network' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'network';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'network_name', NEW.network_name,
            'network_type', NEW.network_type
        );
    ELSIF TG_TABLE_NAME = 'location' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'location';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'location_name', NEW.location_name,
            'location_type', NEW.location_type
        );
    ELSIF TG_TABLE_NAME = 'source_identity' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'source_identity';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'raw_identifier', NEW.raw_identifier,
            'identifier_type', NEW.identifier_type
        );
    ELSIF TG_TABLE_NAME = 'sim' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'sim';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'iccid', NEW.iccid,
            'imsi', NEW.imsi
        );
    END IF;

    IF v_payload IS NOT NULL THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (v_entity_id, 'UPSERT_NODE', v_entity_type, v_payload);
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION civix.trg_upsert_node_outbox IS 'Generic outbox trigger for emitting UPSERT_NODE events for graph entities. Uses explicit allowlist (jsonb_build_object) and SECURITY INVOKER.';

CREATE TRIGGER trg_person_upsert_outbox AFTER INSERT OR UPDATE ON civix.person FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_phone_number_upsert_outbox AFTER INSERT OR UPDATE ON civix.phone_number FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_device_upsert_outbox AFTER INSERT OR UPDATE ON civix.device FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_vehicle_upsert_outbox AFTER INSERT OR UPDATE ON civix.vehicle FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_property_upsert_outbox AFTER INSERT OR UPDATE ON civix.property FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_financial_account_upsert_outbox AFTER INSERT OR UPDATE ON civix.financial_account FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_organization_upsert_outbox AFTER INSERT OR UPDATE ON civix.organization FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_network_upsert_outbox AFTER INSERT OR UPDATE ON civix.network FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_location_upsert_outbox AFTER INSERT OR UPDATE ON civix.location FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_source_identity_upsert_outbox AFTER INSERT OR UPDATE ON civix.source_identity FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_sim_upsert_outbox AFTER INSERT OR UPDATE ON civix.sim FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_investigative_case_upsert_outbox AFTER INSERT OR UPDATE ON civix.investigative_case FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();
CREATE TRIGGER trg_fir_upsert_outbox AFTER INSERT OR UPDATE ON civix.fir FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();

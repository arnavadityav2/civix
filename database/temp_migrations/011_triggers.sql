-- =============================================================================
-- CIVIX Platform — Migration 011: Bitemporal & Append-Only Triggers
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/phase1_audit/GATE3_BITEMPORAL_ENFORCEMENT_STANDARD.md
--            BLK-17/ADR-019: Append-only triggers on bitemporal tables
--            BLK-16/ADR-018: Entity DELETE prohibition
--            INV-13: audit_event is append-only
-- =============================================================================
-- TRIGGER PHILOSOPHY:
--   1. audit_event: Absolute append-only. No UPDATE or DELETE ever.
--   2. entity: No physical DELETE. Use visibility_status = 'TOMBSTONED'.
--   3. hypothesis_support: Bitemporal. UPDATE = close old + insert new.
--   4. case_entity_role: Bitemporal. Same pattern.
--   5. hypothesis: Bitemporal closures (tx_end).
--   6. Outbox: Emitted after state changes for Neo4j CDC.
-- =============================================================================

SET search_path TO civix, public;

-- =============================================================================
-- TRIGGER 1: audit_event — Absolute Append-Only (INV-13)
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_audit_event_append_only()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'CIVIX INVARIANT VIOLATION: audit_event is append-only. UPDATE and DELETE are prohibited. (INV-13)';
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_audit_append_only
    BEFORE UPDATE OR DELETE ON civix.audit_event
    FOR EACH ROW EXECUTE FUNCTION civix.trg_audit_event_append_only();

-- =============================================================================
-- TRIGGER 2: entity — Prohibit Physical DELETE (BLK-16/ADR-018)
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_entity_no_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'CIVIX INVARIANT VIOLATION: Physical deletion of civix.entity rows is prohibited. '
        'Use UPDATE SET visibility_status = ''TOMBSTONED'' instead. (BLK-16, ADR-018) '
        'Entity ID: %', OLD.entity_id;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_entity_no_delete
    BEFORE DELETE ON civix.entity
    FOR EACH ROW EXECUTE FUNCTION civix.trg_entity_no_delete();

-- =============================================================================
-- TRIGGER 3: hypothesis_support — Bitemporal Append-Only (BLK-17/ADR-019)
-- When an UPDATE is attempted on an ACTIVE row (tx_end IS NULL):
--   1. Close the old row: set tx_end = now()
--   2. Insert a new row with updated fields and tx_start = now()
--   3. Return NULL to suppress the original UPDATE
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_hypothesis_support_bitemporal()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Only intercept updates to currently-active rows
    IF OLD.tx_end IS NOT NULL THEN
        RAISE EXCEPTION
            'CIVIX INVARIANT VIOLATION: Cannot UPDATE a closed (historical) hypothesis_support row. '
            'Historical records are immutable. (BLK-17, ADR-019)';
    END IF;

    -- Step 1: Close the old row
    UPDATE civix.hypothesis_support
        SET tx_end = now()
        WHERE support_id = OLD.support_id;

    -- Step 2: Insert new row with updated values and fresh tx_start
    INSERT INTO civix.hypothesis_support (
        hypothesis_id, assertion_id, stance, weight, assigned_by,
        analysis_run_id, tx_start, tx_end
    ) VALUES (
        NEW.hypothesis_id,
        NEW.assertion_id,
        NEW.stance,
        NEW.weight,
        NEW.assigned_by,
        NEW.analysis_run_id,
        now(),
        NULL  -- Active
    );

    -- Step 3: Suppress the original UPDATE
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_hypothesis_support_bitemporal
    BEFORE UPDATE ON civix.hypothesis_support
    FOR EACH ROW EXECUTE FUNCTION civix.trg_hypothesis_support_bitemporal();

-- =============================================================================
-- TRIGGER 4: case_entity_role — Bitemporal Append-Only (BLK-12)
-- Same pattern as hypothesis_support.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_case_entity_role_bitemporal()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.tx_end IS NOT NULL THEN
        RAISE EXCEPTION
            'CIVIX INVARIANT VIOLATION: Cannot UPDATE a closed historical case_entity_role row. '
            'Historical records are immutable. (BLK-12, BLK-17)';
    END IF;

    -- Close old row
    UPDATE civix.case_entity_role
        SET tx_end = now()
        WHERE role_id = OLD.role_id;

    -- Insert new row
    INSERT INTO civix.case_entity_role (
        case_id, entity_id, role, role_basis, assigned_by,
        valid_from, valid_to, tx_start, tx_end
    ) VALUES (
        NEW.case_id, NEW.entity_id, NEW.role, NEW.role_basis, NEW.assigned_by,
        NEW.valid_from, NEW.valid_to, now(), NULL
    );

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_case_entity_role_bitemporal
    BEFORE UPDATE ON civix.case_entity_role
    FOR EACH ROW EXECUTE FUNCTION civix.trg_case_entity_role_bitemporal();

-- =============================================================================
-- TRIGGER 5: Outbox emission on entity tombstoning (BLK-18/ADR-018)
-- When visibility_status changes to 'TOMBSTONED', emit TOMBSTONE_NODE to outbox.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_entity_tombstone_outbox()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.visibility_status = 'TOMBSTONED' AND OLD.visibility_status != 'TOMBSTONED' THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (
            NEW.entity_id,
            'TOMBSTONE_NODE',
            NEW.entity_type::text,
            jsonb_build_object(
                'entity_id', NEW.entity_id,
                'entity_type', NEW.entity_type,
                'tombstoned_at', now()
            )
        );
    ELSIF NEW.visibility_status = 'RESTRICTED' AND OLD.visibility_status = 'ACTIVE' THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (
            NEW.entity_id,
            'DEACTIVATE_NODE',
            NEW.entity_type::text,
            jsonb_build_object(
                'entity_id', NEW.entity_id,
                'entity_type', NEW.entity_type,
                'restricted_at', now()
            )
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_entity_tombstone_outbox
    AFTER UPDATE ON civix.entity
    FOR EACH ROW EXECUTE FUNCTION civix.trg_entity_tombstone_outbox();

-- =============================================================================
-- TRIGGER 6: Outbox emission when hypothesis_support tx_end closes (BLK-18)
-- When a bitemporal row is closed (tx_end set), emit DEACTIVATE_EDGE to Neo4j.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_hypothesis_support_outbox()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    -- Emit event when a support link becomes inactive
    IF NEW.tx_end IS NOT NULL AND OLD.tx_end IS NULL THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (
            NEW.support_id,
            'DEACTIVATE_EDGE',
            'hypothesis_support',
            jsonb_build_object(
                'support_id', NEW.support_id,
                'hypothesis_id', NEW.hypothesis_id,
                'assertion_id', NEW.assertion_id,
                'stance', NEW.stance,
                'closed_at', NEW.tx_end
            )
        );
    -- Emit event when a new support link becomes active
    ELSIF TG_OP = 'INSERT' AND NEW.tx_end IS NULL THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (
            NEW.support_id,
            'UPSERT_EDGE',
            'hypothesis_support',
            jsonb_build_object(
                'support_id', NEW.support_id,
                'hypothesis_id', NEW.hypothesis_id,
                'assertion_id', NEW.assertion_id,
                'stance', NEW.stance,
                'tx_start', NEW.tx_start
            )
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_hypothesis_support_outbox
    AFTER INSERT OR UPDATE ON civix.hypothesis_support
    FOR EACH ROW EXECUTE FUNCTION civix.trg_hypothesis_support_outbox();

-- =============================================================================
-- TRIGGER 7: source_record — Prevent UPDATE (append-only per Bible invariant)
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.trg_source_record_immutable()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'CIVIX INVARIANT VIOLATION: source_record rows are immutable. '
        'Use INSERT with superseded_by to correct a record. '
        'Record ID: %', OLD.source_record_id;
    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_source_record_immutable
    BEFORE UPDATE ON civix.source_record
    FOR EACH ROW EXECUTE FUNCTION civix.trg_source_record_immutable();

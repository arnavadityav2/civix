-- =============================================================================
-- CIVIX Platform — Migration 024: case_entity_role → Neo4j Projection
-- Phase 7 Step 7: Close the architectural gap between Stage 4 entity linking
-- and the Neo4j graph projection.
--
-- Authority: ADR (pending) — case_entity_role HAS_ROLE graph projection
-- Problem:   case_entity_role has no outbox trigger. Entities added via the
--            POST /api/v1/cases/{case_id}/entities endpoint are invisible to
--            the Network workspace because they are never projected to Neo4j.
--
-- Solution:
--   1. Trigger on case_entity_role INSERT/UPDATE to emit UPSERT_EDGE events.
--   2. When tx_end is set (soft-delete), emit DEACTIVATE_EDGE to remove the
--      HAS_ROLE relationship from Neo4j.
--   3. Payload carries all fields needed by Neo4jProjectionService to
--      MERGE the relationship idempotently.
--
-- Idempotency: CDC worker uses seq_no ordering. The projection service will
--   MERGE the (Case)-[:HAS_ROLE {role_id}]->(Entity) relationship and SET
--   properties only if the incoming seq_no is greater than the stored one.
--
-- PostgreSQL remains the source of truth.
-- Neo4j is the graph projection, not a second authoritative database.
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- Ensure tx_start and tx_end columns exist on case_entity_role.
-- These are defined in 007_cases_and_access.sql but may be absent on older
-- test database instances that were created before that migration was applied.
-- ADD COLUMN IF NOT EXISTS is idempotent.
-- ---------------------------------------------------------------------------
ALTER TABLE civix.case_entity_role
    ADD COLUMN IF NOT EXISTS tx_start TIMESTAMPTZ NOT NULL DEFAULT now();

ALTER TABLE civix.case_entity_role
    ADD COLUMN IF NOT EXISTS tx_end TIMESTAMPTZ NULL;

-- Recreate the partial unique index on active roles if it does not exist.
-- This index enforces the business invariant: only one active role per
-- (case, entity, role) combination. Historical rows (tx_end IS NOT NULL)
-- are excluded from uniqueness enforcement.
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_case_entity_role
    ON civix.case_entity_role (case_id, entity_id, role)
    WHERE tx_end IS NULL;

-- ---------------------------------------------------------------------------
-- Trigger function: fires on INSERT or UPDATE of case_entity_role
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION civix.trg_case_entity_role_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
    v_action TEXT;
    v_payload JSONB;
BEGIN
    -- Determine action: if tx_end is being set, this is a soft-delete.
    -- If role is being inserted or updated while still active, UPSERT_EDGE.
    IF NEW.tx_end IS NOT NULL THEN
        v_action := 'DEACTIVATE_EDGE';
    ELSE
        v_action := 'UPSERT_EDGE';
    END IF;

    v_payload := jsonb_build_object(
        'role_id',    NEW.role_id,
        'case_id',    NEW.case_id,
        'entity_id',  NEW.entity_id,
        'role',       NEW.role,
        'role_basis', NEW.role_basis,
        'tx_end',     NEW.tx_end
    );

    INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
    VALUES (NEW.role_id, v_action, 'case_entity_role', v_payload);

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION civix.trg_case_entity_role_outbox IS
    'Outbox trigger for case_entity_role. Emits UPSERT_EDGE (active role) or
     DEACTIVATE_EDGE (tx_end set = soft-delete) to drive Neo4j HAS_ROLE
     projection. Projection is idempotent via seq_no. Migration 024.';

-- Trigger fires on INSERT and on UPDATE of the columns that can change.
-- valid_from/valid_to can update without affecting the projection.
-- The critical columns are role, role_basis (content) and tx_end (lifecycle).
CREATE TRIGGER trg_case_entity_role_outbox
AFTER INSERT OR UPDATE OF role, role_basis, tx_end
ON civix.case_entity_role
FOR EACH ROW
EXECUTE FUNCTION civix.trg_case_entity_role_outbox();

COMMENT ON TRIGGER trg_case_entity_role_outbox ON civix.case_entity_role IS
    'CDC trigger: drives Neo4j HAS_ROLE projection for case-entity links.
     Migration 024.';

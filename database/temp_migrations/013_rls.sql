-- =============================================================================
-- CIVIX Platform — Migration 013: Row-Level Security (RLS)
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/phase1_audit/GATE3_AUTHORIZATION_BOUNDARY_STANDARD.md
--            BLK-15/ADR-017: assertion.authorized_case_ids RLS
--            BLK-07: Cross-case isolation
--            INV-12: Legal restrictions ≠ deletion
-- =============================================================================
-- RLS DESIGN PRINCIPLES:
--   1. FAIL CLOSED: Empty authorized_case_ids = invisible assertion.
--   2. Row-level security is enforced at the database layer, NOT only at the API.
--   3. An authorized signatory does NOT become an owner through transaction access.
--   4. Restricted entities remain in PostgreSQL but are invisible to most users.
--   5. RLS policies reference civix.case_access for live authorization.
-- =============================================================================
-- NOTE: RLS policies require application code to SET app.current_user_id
--       before executing queries. This is the session-level variable used by RLS.
--       In production: SET LOCAL app.current_user_id = '<uuid>'
--       This is enforced at the connection/session middleware layer.
-- =============================================================================

SET search_path TO civix, public;

-- =============================================================================
-- ENABLE RLS ON PROTECTED TABLES
-- =============================================================================

ALTER TABLE civix.investigative_case   ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.evidence_instance    ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.assertion            ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.hypothesis           ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.hypothesis_support   ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.investigative_lead   ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.investigation_task   ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.case_entity_role     ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.fir                  ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- HELPER FUNCTION: Get current user's accessible case IDs
-- Used by multiple RLS policies to avoid code duplication.
-- Returns the set of case_ids the current session user can access.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.get_accessible_case_ids()
RETURNS UUID[] LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT COALESCE(
        ARRAY(
            SELECT ca.case_id
            FROM civix.case_access ca
            WHERE ca.user_id = current_setting('app.current_user_id', TRUE)::uuid
              AND ca.is_revoked = FALSE
              AND (ca.valid_until IS NULL OR ca.valid_until > now())
        ),
        '{}'::UUID[]
    );
$$;

COMMENT ON FUNCTION civix.get_accessible_case_ids IS
    'Returns the array of case_ids accessible to the current session user. '
    'Requires app.current_user_id to be set in session. Fails closed (returns empty array) if not set.';

-- =============================================================================
-- HELPER FUNCTION: Is current user an ADMIN or SUPERVISOR?
-- Admins/Supervisors bypass some but not all RLS restrictions.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.current_user_is_admin()
RETURNS BOOLEAN LANGUAGE sql STABLE SECURITY DEFINER AS $$
    SELECT EXISTS (
        SELECT 1 FROM civix.civix_user
        WHERE user_id = current_setting('app.current_user_id', TRUE)::uuid
          AND role IN ('ADMIN', 'SUPERVISOR')
          AND is_active = TRUE
    );
$$;

-- =============================================================================
-- RLS POLICY: investigative_case
-- User can see a case only if they have an active, non-revoked access grant.
-- =============================================================================

-- Allow users to see cases they have access to
CREATE POLICY policy_case_access ON civix.investigative_case
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- Allow case creation by authenticated users with WRITE or ADMIN role
CREATE POLICY policy_case_write ON civix.investigative_case
    FOR INSERT
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM civix.civix_user
            WHERE user_id = current_setting('app.current_user_id', TRUE)::uuid
              AND role IN ('INVESTIGATOR', 'SUPERVISOR', 'ADMIN')
              AND is_active = TRUE
        )
    );

-- =============================================================================
-- RLS POLICY: evidence_instance
-- Scoped by case_id. Case access grant = instance visibility.
-- =============================================================================

CREATE POLICY policy_evidence_instance_select ON civix.evidence_instance
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: assertion
-- BLK-15/ADR-017: Uses materialized authorized_case_ids[] for O(1) RLS check.
-- No recursive provenance traversal. FAIL CLOSED: empty array = invisible.
-- =============================================================================

CREATE POLICY policy_assertion_select ON civix.assertion
    FOR SELECT
    USING (
        -- Array overlap: user's accessible cases intersect with assertion's authorized cases
        authorized_case_ids && civix.get_accessible_case_ids()
        OR civix.current_user_is_admin()
    );

COMMENT ON POLICY policy_assertion_select ON civix.assertion IS
    'O(1) RLS via GIN-indexed authorized_case_ids array. No recursive provenance traversal. '
    'Fails closed: empty authorized_case_ids = no visibility. BLK-15, ADR-017.';

-- =============================================================================
-- RLS POLICY: hypothesis
-- Scoped by case_id (hypotheses belong to a case).
-- =============================================================================

CREATE POLICY policy_hypothesis_select ON civix.hypothesis
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: hypothesis_support
-- Visible if the underlying hypothesis is visible (join-based check).
-- Using EXISTS for clarity; may be optimized with materialized case_id later.
-- =============================================================================

CREATE POLICY policy_hyp_support_select ON civix.hypothesis_support
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM civix.hypothesis h
            WHERE h.hypothesis_id = hypothesis_support.hypothesis_id
              AND h.case_id = ANY(civix.get_accessible_case_ids())
        )
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: investigative_lead
-- =============================================================================

CREATE POLICY policy_lead_select ON civix.investigative_lead
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: investigation_task
-- =============================================================================

CREATE POLICY policy_task_select ON civix.investigation_task
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: case_entity_role
-- =============================================================================

CREATE POLICY policy_case_entity_role_select ON civix.case_entity_role
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- RLS POLICY: fir
-- =============================================================================

CREATE POLICY policy_fir_select ON civix.fir
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- =============================================================================
-- FUNCTION: Populate authorized_case_ids when an assertion is linked to an instance
-- This is the mechanism for BLK-15: when an extraction → assertion is created
-- from an evidence_instance in case X, append case X to assertion.authorized_case_ids.
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.append_case_to_assertion(
    p_assertion_id UUID,
    p_case_id      UUID
) RETURNS VOID LANGUAGE sql AS $$
    UPDATE civix.assertion
    SET authorized_case_ids = ARRAY(
        SELECT DISTINCT unnest(authorized_case_ids || ARRAY[p_case_id])
    )
    WHERE assertion_id = p_assertion_id
      AND NOT (authorized_case_ids @> ARRAY[p_case_id]);
$$;

COMMENT ON FUNCTION civix.append_case_to_assertion IS
    'Appends a case_id to assertion.authorized_case_ids when evidence from that case '
    'contributes to the assertion. Called by ingestion layer when creating assertion-evidence links. BLK-15.';

-- =============================================================================
-- FUNCTION: Remove case access from an assertion (called on case_access revocation)
-- =============================================================================

CREATE OR REPLACE FUNCTION civix.revoke_case_from_assertion(
    p_assertion_id UUID,
    p_case_id      UUID
) RETURNS VOID LANGUAGE sql AS $$
    UPDATE civix.assertion
    SET authorized_case_ids = ARRAY(
        SELECT unnest(authorized_case_ids)
        EXCEPT SELECT p_case_id
    )
    WHERE assertion_id = p_assertion_id;
$$;

COMMENT ON FUNCTION civix.revoke_case_from_assertion IS
    'Removes a case_id from assertion.authorized_case_ids on evidence restriction. '
    'Called by the access management layer when a case instance is sealed/expunged. BLK-15.';

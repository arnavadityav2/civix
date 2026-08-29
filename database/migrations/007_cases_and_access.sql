-- =============================================================================
-- CIVIX Platform — Migration 007: Cases & Access Control
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 09
--            ADR-003: Physical name is investigative_case (SQL keyword avoidance)
--            BLK-07: Cross-case information boundaries
--            BLK-12: case_entity_role temporal model
--            BLK-15/ADR-017: assertion.authorized_case_ids (RLS performance)
--            Gate 3: Partial UNIQUE index on case_access (vs full UNIQUE)
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.investigative_case
-- Physical name avoids SQL CASE keyword (ADR-003).
-- ---------------------------------------------------------------------------
CREATE TABLE civix.investigative_case (
    case_id              UUID                      PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number          TEXT                      NOT NULL UNIQUE,   -- Format: CIV-2026-001
    title                TEXT                      NOT NULL,
    case_type            civix.case_type_enum      NOT NULL,
    status               civix.case_status_enum    NOT NULL DEFAULT 'OPEN',
    priority             civix.case_priority_enum  NOT NULL DEFAULT 'MEDIUM',
    jurisdiction         TEXT                      NOT NULL,
    investigating_unit   TEXT                      NULL,
    opened_at            DATE                      NOT NULL,
    closed_at            DATE                      NULL,
    lead_investigator_id UUID                      NULL REFERENCES civix.civix_user(user_id),
    created_at           TIMESTAMPTZ               NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ               NOT NULL DEFAULT now(),

    CONSTRAINT chk_case_closed_after_opened
        CHECK (closed_at IS NULL OR closed_at >= opened_at)
);

COMMENT ON TABLE civix.investigative_case IS
    'Central case record. Named investigative_case to avoid SQL keyword. Physical case number format: CIV-YYYY-NNN. ADR-003.';

-- Deferred FK: evidence_instance.case_id → investigative_case
ALTER TABLE civix.evidence_instance
    ADD CONSTRAINT fk_evidence_instance_case
    FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);

-- ---------------------------------------------------------------------------
-- civix.case_entity_role
-- Tracks what role an entity plays in a case (SUSPECT, VICTIM, etc.)
-- BLK-12: Must be bitemporal — role transitions must be preserved.
-- CONTRADICTION-01 NOTE: Bible shows UNIQUE(case_id, entity_id, role).
-- BLK-12 Gate 3 mandates bitemporal tracking → partial index instead.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.case_entity_role (
    role_id      UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id      UUID                        NOT NULL REFERENCES civix.investigative_case(case_id),
    entity_id    UUID                        NOT NULL REFERENCES civix.entity(entity_id),
    role         civix.case_entity_role_enum NOT NULL,
    role_basis   TEXT                        NULL,    -- Justification for role assignment
    assigned_by  UUID                        NULL REFERENCES civix.civix_user(user_id),
    valid_from   DATE                        NULL,
    valid_to     DATE                        NULL,
    -- BLK-12/Gate 3: bitemporal fields
    tx_start     TIMESTAMPTZ                 NOT NULL DEFAULT now(),
    tx_end       TIMESTAMPTZ                 NULL     -- NULL = currently active
);

-- PARTIAL unique index: only one ACTIVE role per (case, entity, role) at a time.
-- Historical (tx_end IS NOT NULL) rows are excluded from uniqueness check.
CREATE UNIQUE INDEX uq_active_case_entity_role
    ON civix.case_entity_role (case_id, entity_id, role)
    WHERE tx_end IS NULL;

COMMENT ON TABLE civix.case_entity_role IS
    'Entity role in a case. Bitemporal: role changes are preserved, not overwritten. Partial unique index on active roles only. BLK-12.';

-- ---------------------------------------------------------------------------
-- civix.fir — First Information Report
-- ---------------------------------------------------------------------------
CREATE TABLE civix.fir (
    fir_id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id              UUID        NOT NULL REFERENCES civix.investigative_case(case_id),
    fir_number           TEXT        NOT NULL,
    police_station       TEXT        NOT NULL,
    district             TEXT        NOT NULL,
    filed_at             TIMESTAMPTZ NOT NULL,
    filed_by             UUID        NULL REFERENCES civix.civix_user(user_id),
    complainant_entity_id UUID       NULL REFERENCES civix.entity(entity_id),
    sections_invoked     TEXT[]      NULL,   -- IPC/BNS section numbers
    source_record_id     UUID        NULL REFERENCES civix.source_record(source_record_id)
);

-- ---------------------------------------------------------------------------
-- civix.case_access
-- Who can access which case and at what permission level.
-- BLK-07/Gate 2: Partial unique index — not full UNIQUE (allows historical records).
-- CONTRADICTION-01: Bible shows UNIQUE(case_id, user_id) — resolved here with partial index.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.case_access (
    access_id        UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id          UUID                     NOT NULL REFERENCES civix.investigative_case(case_id),
    user_id          UUID                     NOT NULL REFERENCES civix.civix_user(user_id),
    permission_level civix.case_permission_enum NOT NULL,
    granted_by       UUID                     NOT NULL REFERENCES civix.civix_user(user_id),
    granted_at       TIMESTAMPTZ              NOT NULL DEFAULT now(),
    valid_until      TIMESTAMPTZ              NULL,    -- NULL = unlimited; time-limited access supported
    is_revoked       BOOLEAN                  NOT NULL DEFAULT FALSE,
    revoked_by       UUID                     NULL REFERENCES civix.civix_user(user_id),
    revoked_at       TIMESTAMPTZ              NULL
);

-- PARTIAL unique index: only one active (non-revoked, non-expired) grant per user-case.
-- Historical revoked/expired records are excluded.
-- Security: Fails closed. No grant = no access.
CREATE UNIQUE INDEX uq_active_case_access
    ON civix.case_access (case_id, user_id)
    WHERE is_revoked = FALSE;

COMMENT ON TABLE civix.case_access IS
    'Per-case access grants. Partial unique index allows historical revoked records. Fails closed — no grant = no access. BLK-07, Gate 3.';

-- ---------------------------------------------------------------------------
-- civix.case_link
-- Controlled cross-case information sharing.
-- BLK-07: Sharing a lead exposes ONLY the lead text and conclusion.
-- It does NOT automatically expose the underlying restricted evidence/assertions.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.case_link (
    link_id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_case_id    UUID        NOT NULL REFERENCES civix.investigative_case(case_id),
    target_case_id    UUID        NOT NULL REFERENCES civix.investigative_case(case_id),
    linked_object_type TEXT       NOT NULL,   -- 'INVESTIGATIVE_LEAD', 'ASSERTION', etc.
    linked_object_id  UUID        NOT NULL,
    share_scope       TEXT        NOT NULL,   -- 'LEAD_ONLY', 'ASSERTION_AND_EVIDENCE', etc.
    authorized_by     UUID        NOT NULL REFERENCES civix.civix_user(user_id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_different_cases CHECK (source_case_id != target_case_id)
);

COMMENT ON TABLE civix.case_link IS
    'Controlled cross-case sharing. share_scope determines what is visible. A LEAD_ONLY share does NOT expose underlying restricted assertions. BLK-07.';

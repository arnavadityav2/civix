-- =============================================================================
-- CIVIX Platform — Migration 032: Event Location Junction Model & RLS
-- Authority: Phase 11B Final Architecture Decision & Phase 11C Execution
-- =============================================================================

SET search_path TO civix, public;

CREATE TABLE IF NOT EXISTS civix.event_location (
    event_location_id  UUID                        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id           UUID                        NOT NULL REFERENCES civix.event(event_id) ON DELETE CASCADE,
    location_id        UUID                        NOT NULL REFERENCES civix.location(entity_id) ON DELETE CASCADE,
    location_predicate civix.predicate_enum        NOT NULL DEFAULT 'LOCATED_AT',
    epistemic_status   civix.epistemic_status_enum NOT NULL DEFAULT 'PROBABLE',
    case_id            UUID                        NOT NULL REFERENCES civix.investigative_case(case_id) ON DELETE CASCADE,
    source_record_id   UUID                        NULL REFERENCES civix.source_record(source_record_id) ON DELETE CASCADE,
    generation_run_id  UUID                        NULL,
    created_at         TIMESTAMPTZ                 NOT NULL DEFAULT now(),

    CONSTRAINT chk_event_location_predicate CHECK (
        location_predicate IN (
            'LOCATED_AT', 'SEEN_AT', 'PRESENT_AT', 'RESIDED_AT', 
            'VISITED', 'ALIBI_CONFIRMED_AT', 'REGISTERED_AT', 'PINGED_TOWER'
        )
    ),
    CONSTRAINT uq_event_location_predicate UNIQUE (event_id, location_id, location_predicate)
);

CREATE INDEX IF NOT EXISTS idx_event_location_event_id ON civix.event_location(event_id);
CREATE INDEX IF NOT EXISTS idx_event_location_location_id ON civix.event_location(location_id);
CREATE INDEX IF NOT EXISTS idx_event_location_case_id ON civix.event_location(case_id);

COMMENT ON TABLE civix.event_location IS
    'Canonical spatial anchoring table linking events to PostGIS locations using CIVIX predicate and epistemic ENUMs. Includes case_id for O(1) RLS scoping.';

-- Enable Row-Level Security
ALTER TABLE civix.event_location ENABLE ROW LEVEL SECURITY;

-- RLS Select Policy (Idempotent)
DROP POLICY IF EXISTS policy_event_location_select ON civix.event_location;
CREATE POLICY policy_event_location_select ON civix.event_location
    FOR SELECT
    USING (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

-- RLS Insert Policy (Idempotent)
DROP POLICY IF EXISTS policy_event_location_write ON civix.event_location;
CREATE POLICY policy_event_location_write ON civix.event_location
    FOR INSERT
    WITH CHECK (
        case_id = ANY(civix.get_accessible_case_ids())
        OR civix.current_user_is_admin()
    );

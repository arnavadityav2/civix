-- =============================================================================
-- CIVIX Platform — Migration 005: Identity Resolution Model
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 05 (Identity)
--            Architecture Principle: identity is NEVER auto-merged (P-04)
--            INV-07: Person never auto-created from SourceIdentity
-- =============================================================================
-- IMPORTANT: Merging/splitting source identities is a human decision ALWAYS.
-- Even at confidence = 0.9999. The DB enforces this via decided_by FK.
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.analysis_run
-- Tracks AI model executions. Placed here because identity_candidate FKs to it.
-- Also used by extraction (migration 008).
-- ---------------------------------------------------------------------------
CREATE TABLE civix.analysis_run (
    run_id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name               TEXT        NOT NULL,
    model_version            TEXT        NOT NULL,
    algorithm_type           TEXT        NOT NULL,
    algorithm_parameters     JSONB       NULL,
    input_snapshot_hash      BYTEA       NULL,   -- Hash of the input dataset state
    input_snapshot_tx_time   TIMESTAMPTZ NULL,   -- AS-OF time for the input snapshot (ML leakage guard)
    started_at               TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at              TIMESTAMPTZ NULL,
    initiated_by             UUID        NULL REFERENCES civix.civix_user(user_id),
    generation_run_id        UUID        NULL REFERENCES civix.generation_run(run_id)
);

COMMENT ON TABLE civix.analysis_run IS
    'Tracks an AI/ML model execution. input_snapshot_tx_time prevents future-data leakage in ML training. GATE3_ML_TEMPORAL_LEAKAGE_AUDIT.';

-- ---------------------------------------------------------------------------
-- civix.identity_candidate
-- AI proposes a match between a source_identity and a canonical person.
-- All candidates require human review — no auto-accept.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.identity_candidate (
    candidate_id      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    source_identity_id UUID          NOT NULL REFERENCES civix.source_identity(entity_id),
    proposed_person_id UUID          NOT NULL REFERENCES civix.person(entity_id),
    ai_confidence     DECIMAL(5,4)   NOT NULL CHECK (ai_confidence BETWEEN 0.0 AND 1.0),
    analysis_run_id   UUID           NOT NULL REFERENCES civix.analysis_run(run_id),
    is_active         BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT now(),

    CONSTRAINT uq_identity_candidate UNIQUE (source_identity_id, proposed_person_id)
);
-- Multiple active candidates per source_identity ARE ALLOWED and expected.
-- A source_identity may have candidates for multiple persons simultaneously.
-- INV-07: Person entity is never auto-created from SourceIdentity.

-- ---------------------------------------------------------------------------
-- civix.identity_resolution
-- Human decision on which candidate (if any) is accepted.
-- IMMUTABLE via superseded_by self-reference pattern.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.identity_resolution (
    resolution_id       UUID                               PRIMARY KEY DEFAULT gen_random_uuid(),
    source_identity_id  UUID                               NOT NULL REFERENCES civix.source_identity(entity_id),
    candidate_id        UUID                               NULL REFERENCES civix.identity_candidate(candidate_id),
    resolved_person_id  UUID                               NULL REFERENCES civix.person(entity_id),
    status              civix.identity_resolution_status_enum NOT NULL,
    decided_by          UUID                               NULL REFERENCES civix.civix_user(user_id),
    decision_notes      TEXT                               NULL,
    superseded_by       UUID                               NULL REFERENCES civix.identity_resolution(resolution_id),
    tx_start            TIMESTAMPTZ                        NOT NULL DEFAULT now(),
    tx_end              TIMESTAMPTZ                        NULL,

    CONSTRAINT chk_resolution_accepted
        CHECK (status != 'ACCEPTED' OR resolved_person_id IS NOT NULL)
    -- If ACCEPTED, must have a resolved_person_id.
    -- P-04: Even at confidence 0.9999, a human must decide.
);
-- INVARIANT: Never UPDATE. Corrections insert new row + set superseded_by on old row.

COMMENT ON TABLE civix.identity_resolution IS
    'Human decision linking a source_identity to a canonical person. Append-only (superseded_by chain). P-04: human required always, no auto-merge.';

-- ---------------------------------------------------------------------------
-- civix.identity_merge_event
-- Records when two source identities were merged into one canonical person.
-- IMMUTABLE: No UPDATE or DELETE ever.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.identity_merge_event (
    merge_event_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source_identity_a   UUID        NOT NULL REFERENCES civix.source_identity(entity_id),
    source_identity_b   UUID        NOT NULL REFERENCES civix.source_identity(entity_id),
    merged_into_person_id UUID      NOT NULL REFERENCES civix.person(entity_id),
    resolution_id       UUID        NOT NULL REFERENCES civix.identity_resolution(resolution_id),
    decided_by          UUID        NOT NULL REFERENCES civix.civix_user(user_id),
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason              TEXT        NULL,

    CONSTRAINT chk_different_identities
        CHECK (source_identity_a != source_identity_b)
);
-- INVARIANT: IMMUTABLE. No UPDATE or DELETE.

COMMENT ON TABLE civix.identity_merge_event IS
    'Immutable record of two source identities being merged into one person. Historical assertions remain valid for each source identity. INV-07.';

-- ---------------------------------------------------------------------------
-- civix.identity_split_event
-- Records when a previously merged identity was split into two persons.
-- IMMUTABLE: No UPDATE or DELETE ever.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.identity_split_event (
    split_event_id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    original_resolution_id   UUID        NOT NULL REFERENCES civix.identity_resolution(resolution_id),
    split_source_identity_a  UUID        NOT NULL REFERENCES civix.source_identity(entity_id),
    split_source_identity_b  UUID        NOT NULL REFERENCES civix.source_identity(entity_id),
    new_person_b_id          UUID        NOT NULL REFERENCES civix.person(entity_id),
    decided_by               UUID        NOT NULL REFERENCES civix.civix_user(user_id),
    reason                   TEXT        NOT NULL,
    occurred_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- INVARIANT: IMMUTABLE.
-- When a split occurs, historical assertions derived before the split remain
-- associated with the original source_identity rows. They are NOT retroactively
-- reassigned. This preserves the epistemic audit trail.

COMMENT ON TABLE civix.identity_split_event IS
    'Immutable record of an identity split. Historical assertions are NOT rewritten — they remain on the original source_identity. This is a core epistemic invariant.';

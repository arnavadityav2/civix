-- =============================================================================
-- CIVIX Platform — Migration 008: Epistemic Pipeline
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 10
--            docs/05_EPISTEMIC_MODEL.md
--            ADR-002: Assertion has no stance (INV-01)
--            ADR-021: No entity FKs on event table (INV-05)
--            BLK-06/ADR-019: Bitemporal hypothesis_support (partial unique index)
--            BLK-09: N-ary event participant model (UNIQUE on event+entity+role)
--            BLK-15/ADR-017: assertion.authorized_case_ids UUID[]
--            INV-08: AI cannot autonomously confirm a hypothesis
-- =============================================================================
-- EPISTEMIC PIPELINE (canonical):
--   Evidence → Observation → Extraction → Event → Assertion → Hypothesis
--   (Each layer is strictly separated. Do NOT collapse.)
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.observation
-- A raw observation made from an evidence_instance.
-- IMMUTABLE: corrections create new rows.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.observation (
    observation_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id       UUID        NOT NULL REFERENCES civix.evidence_instance(instance_id),
    observer_type     TEXT        NOT NULL,   -- HUMAN, AI_MODEL, AUTOMATED_SYSTEM
    observed_by       UUID        NULL REFERENCES civix.civix_user(user_id),
    -- NULL if observer_type = AI_MODEL (use analysis_run instead)
    observation_type  TEXT        NULL,       -- Free-form type for now; structured later
    observation_text  TEXT        NULL,
    structured_content JSONB      NULL,
    observed_at       TIMESTAMPTZ NOT NULL,   -- Real-world time of observation
    tx_start          TIMESTAMPTZ NOT NULL DEFAULT now()
    -- IMMUTABLE: No UPDATE or DELETE. Corrections create new observation rows.
);

COMMENT ON TABLE civix.observation IS
    'Immutable raw observation from an evidence_instance. Corrections create new rows. Epistemic layer 1.';

-- ---------------------------------------------------------------------------
-- civix.extraction
-- AI/human-derived structured entity extraction from an evidence instance.
-- Superseded_by pattern for corrections.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.extraction (
    extraction_id     UUID                       PRIMARY KEY DEFAULT gen_random_uuid(),
    instance_id       UUID                       NOT NULL REFERENCES civix.evidence_instance(instance_id),
    analysis_run_id   UUID                       NOT NULL REFERENCES civix.analysis_run(run_id),
    extraction_type   civix.extraction_type_enum NOT NULL,
    extracted_value   JSONB                      NOT NULL,
    ai_confidence     DECIMAL(5,4)               NOT NULL CHECK (ai_confidence BETWEEN 0.0 AND 1.0),
    is_superseded     BOOLEAN                    NOT NULL DEFAULT FALSE,
    superseded_by     UUID                       NULL REFERENCES civix.extraction(extraction_id),
    tx_start          TIMESTAMPTZ                NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- civix.event
-- Represents a real-world event. NO entity FKs on this table (ADR-021/INV-05).
-- All entity participation goes through event_participant.
-- occurred_at is TSTZRANGE (not scalar) to support temporal uncertainty.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.event (
    event_id          UUID                    PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type        civix.event_type_enum   NOT NULL,
    occurred_at       TSTZRANGE               NOT NULL,
    -- TSTZRANGE = real-world time interval with uncertainty support
    -- e.g. "[2026-06-15 14:00, 2026-06-15 14:30)" for an observed meeting
    description       TEXT                    NULL,
    source_record_id  UUID                    NULL REFERENCES civix.source_record(source_record_id),
    tx_start          TIMESTAMPTZ             NOT NULL DEFAULT now(),
    generation_run_id UUID                    NULL REFERENCES civix.generation_run(run_id)
);
-- NO location_id FK, NO subject_id, NO sender_id, NO receiver_id columns.
-- ALL entity relationships use event_participant.
-- Location is event_participant(participant_role=LOCATION).

COMMENT ON TABLE civix.event IS
    'Real-world event. occurred_at is TSTZRANGE for temporal uncertainty. NO entity FKs — all via event_participant. Location is a participant with role=LOCATION. ADR-021, INV-05.';

-- ---------------------------------------------------------------------------
-- civix.event_participant — N-ary Event Model
-- Authority: BLK-09, ADR-021
-- H4 scenario: one PROPERTY_MUTATION event → two TARGET_PROPERTY participants
-- ---------------------------------------------------------------------------
CREATE TABLE civix.event_participant (
    participant_id    UUID                       PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id          UUID                       NOT NULL REFERENCES civix.event(event_id),
    entity_id         UUID                       NOT NULL REFERENCES civix.entity(entity_id),
    participant_role  civix.participant_role_enum NOT NULL,
    role_confidence   DECIMAL(5,4)               NULL CHECK (role_confidence BETWEEN 0.0 AND 1.0),
    tx_start          TIMESTAMPTZ                NOT NULL DEFAULT now(),

    -- BLK-21/ADR-022: UNIQUE on (event, entity, role) — allows same entity with multiple roles
    -- e.g. Person X is simultaneously REGISTERED_OWNER and DRIVER in one event
    -- But NOT two rows with identical (event_id, entity_id, participant_role)
    CONSTRAINT uq_event_participant UNIQUE (event_id, entity_id, participant_role)
);

COMMENT ON TABLE civix.event_participant IS
    'N-ary event participant. UNIQUE on (event, entity, role) allows one entity with multiple roles (e.g. OWNER + DRIVER). H4: two TARGET_PROPERTY participants on one PROPERTY_MUTATION event. BLK-09, BLK-21.';

-- ---------------------------------------------------------------------------
-- civix.assertion
-- A structured claim: subject → predicate → object.
-- BLK-15/ADR-017: authorized_case_ids[] for efficient RLS without recursive joins.
-- INV-01/ADR-002: NO stance column — stance lives in hypothesis_support.
-- Subject must be a SourceIdentity (not EntityCluster — INV-02).
-- ---------------------------------------------------------------------------
CREATE TABLE civix.assertion (
    assertion_id           UUID                      PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_entity_id      UUID                      NOT NULL REFERENCES civix.entity(entity_id),
    -- Must target source_identity (INV-02: never EntityCluster)
    -- Enforced at application layer; entity.entity_type checked on INSERT
    predicate              civix.predicate_enum      NOT NULL,
    -- INV-18: Free-text predicates BANNED. Only predicate_enum values permitted.
    object_entity_id       UUID                      NULL REFERENCES civix.entity(entity_id),
    object_value           TEXT                      NULL,    -- For scalar assertions
    object_location_id     UUID                      NULL REFERENCES civix.location(entity_id),
    epistemic_status       civix.epistemic_status_enum NOT NULL,
    ai_confidence          DECIMAL(5,4)              NULL CHECK (ai_confidence BETWEEN 0.0 AND 1.0),
    asserted_by            UUID                      NULL REFERENCES civix.civix_user(user_id),
    source_analysis_run_id UUID                      NULL REFERENCES civix.analysis_run(run_id),
    valid_from             TIMESTAMPTZ               NULL,    -- Real-world validity start
    valid_to               TIMESTAMPTZ               NULL,    -- Real-world validity end
    tx_start               TIMESTAMPTZ               NOT NULL DEFAULT now(),
    tx_end                 TIMESTAMPTZ               NULL,
    generation_run_id      UUID                      NULL REFERENCES civix.generation_run(run_id),

    -- BLK-15/ADR-017: materialized case authorization array
    -- Populated by trigger when evidence_instance → observation → extraction → assertion
    -- RLS policy uses: authorized_case_ids && (user's case list)
    -- Must be kept in sync when case_access changes
    authorized_case_ids    UUID[]                    NOT NULL DEFAULT '{}',

    CONSTRAINT chk_assertion_has_object
        CHECK (object_entity_id IS NOT NULL
            OR object_value IS NOT NULL
            OR object_location_id IS NOT NULL),

    CONSTRAINT chk_assertion_has_assertor
        CHECK (asserted_by IS NOT NULL OR source_analysis_run_id IS NOT NULL)
);
-- INV-01: NO stance column here. Stance = hypothesis_support.stance.
-- INV-02: subject_entity_id should reference a SOURCE_IDENTITY entity.
--         Enforced via application layer check: entity.entity_type = 'SOURCE_IDENTITY'.
--         (Cannot enforce with FK alone since entity can be any type.)

COMMENT ON TABLE civix.assertion IS
    'Structured S-P-O claim. NO stance (INV-01). authorized_case_ids[] enables O(1) RLS without recursive provenance traversal. BLK-15, ADR-017. Predicate is enum-only (INV-18).';

-- ---------------------------------------------------------------------------
-- civix.hypothesis
-- An investigative theory about a case. INVESTIGATOR-CONTROLLED only.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.hypothesis (
    hypothesis_id   UUID                          PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id         UUID                          NOT NULL REFERENCES civix.investigative_case(case_id),
    hypothesis_text TEXT                          NOT NULL,
    status          civix.hypothesis_status_enum  NOT NULL DEFAULT 'ACTIVE',
    created_by      UUID                          NOT NULL REFERENCES civix.civix_user(user_id),
    confirmed_by    UUID                          NULL REFERENCES civix.civix_user(user_id),
    tx_start        TIMESTAMPTZ                   NOT NULL DEFAULT now(),
    tx_end          TIMESTAMPTZ                   NULL,

    -- INV-08: AI cannot autonomously confirm a hypothesis.
    -- confirmed_by MUST be a human user if status = CONFIRMED.
    CONSTRAINT chk_hypothesis_human_confirmation
        CHECK (status != 'CONFIRMED' OR confirmed_by IS NOT NULL)
);

COMMENT ON TABLE civix.hypothesis IS
    'Investigative hypothesis. AI may NOT set status=CONFIRMED (INV-08, DB CHECK constraint). Only human (confirmed_by) can confirm.';

-- ---------------------------------------------------------------------------
-- civix.hypothesis_support
-- Links an assertion to a hypothesis with a directional stance.
-- BLK-06/ADR-019: Bitemporal. Historical stance changes PRESERVED.
-- CONTRADICTION-02: Bible shows UNIQUE(hypothesis_id, assertion_id).
--   Gate 3 BLK-06 mandates partial index for bitemporal tracking.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.hypothesis_support (
    support_id      UUID                     PRIMARY KEY DEFAULT gen_random_uuid(),
    hypothesis_id   UUID                     NOT NULL REFERENCES civix.hypothesis(hypothesis_id),
    assertion_id    UUID                     NOT NULL REFERENCES civix.assertion(assertion_id),
    stance          civix.support_stance_enum NOT NULL,
    -- INV-01: Stance is HERE, not on assertion.
    weight          DECIMAL(5,4)             NOT NULL DEFAULT 1.0 CHECK (weight BETWEEN 0.0 AND 1.0),
    assigned_by     UUID                     NULL REFERENCES civix.civix_user(user_id),
    analysis_run_id UUID                     NULL REFERENCES civix.analysis_run(run_id),
    tx_start        TIMESTAMPTZ              NOT NULL DEFAULT now(),
    tx_end          TIMESTAMPTZ              NULL    -- NULL = currently active
    -- valid_from/valid_to not needed: stance is a DB-time claim, not a real-world-time claim
);

-- CONTRADICTION-02 RESOLUTION: Partial UNIQUE index (not full UNIQUE).
-- Only one ACTIVE (tx_end IS NULL) support per (hypothesis, assertion) pair.
-- Historical (tx_end IS NOT NULL) records are excluded → AS-OF queries work correctly.
CREATE UNIQUE INDEX uq_active_hypothesis_support
    ON civix.hypothesis_support (hypothesis_id, assertion_id)
    WHERE tx_end IS NULL;

COMMENT ON TABLE civix.hypothesis_support IS
    'Directional stance link between assertion and hypothesis. Bitemporal: stance changes create new rows, old preserved. Partial unique index on active only. BLK-06, ADR-019.';

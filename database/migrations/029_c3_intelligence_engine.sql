-- =============================================================================
-- CIVIX Platform — Migration 029: C3 Intelligence Engine
-- Phase C3 Implementation
-- Authority: svgC3_Intelligence_Engine_Planning_Audit.md
-- =============================================================================
-- C3 adds:
--   1. investigative_lead  — 4 new nullable columns (feature_vector_version,
--                            deterministic_findings, explanation, explanation_status)
--   2. investigative_finding — relational finding table with provenance
--   3. Indexes for C3 query patterns
--   4. Updated outbox trigger to include new payload fields
-- =============================================================================
-- SAFETY: All new columns are NULLABLE. Existing data is unaffected.
-- REPEAT-SAFE: Uses ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS.
-- C1/C2 tables: UNTOUCHED.
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- 1. ALTER civix.investigative_lead — Add C3 columns
-- ---------------------------------------------------------------------------
ALTER TABLE civix.investigative_lead
    ADD COLUMN IF NOT EXISTS feature_vector_version  TEXT             NULL,
    ADD COLUMN IF NOT EXISTS deterministic_findings  JSONB            NULL DEFAULT '[]'::jsonb,
    ADD COLUMN IF NOT EXISTS explanation             JSONB            NULL,
    ADD COLUMN IF NOT EXISTS explanation_status      TEXT             NULL;

-- Constraint: explanation_status must be one of the approved values (or NULL)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = 'civix'
          AND table_name   = 'investigative_lead'
          AND constraint_name = 'chk_lead_explanation_status'
    ) THEN
        ALTER TABLE civix.investigative_lead
            ADD CONSTRAINT chk_lead_explanation_status
            CHECK (explanation_status IS NULL OR explanation_status IN (
                'VALID', 'REJECTED', 'SKIPPED', 'PENDING'
            ));
    END IF;
END;
$$;

COMMENT ON COLUMN civix.investigative_lead.feature_vector_version IS
    'Version string of the 70-feature schema used to generate this lead (e.g. behavioral_xgboost_v1). C3.';
COMMENT ON COLUMN civix.investigative_lead.deterministic_findings IS
    'JSON array of DeterministicFinding records that support this lead. C3. No LLM-generated content.';
COMMENT ON COLUMN civix.investigative_lead.explanation IS
    'Validated Gemini explanation JSONB. NULL if explanation_status is SKIPPED or REJECTED. C3.';
COMMENT ON COLUMN civix.investigative_lead.explanation_status IS
    'VALID | REJECTED | SKIPPED | PENDING. REJECTED = hallucination detected. SKIPPED = Gemini unavailable. C3.';

-- ---------------------------------------------------------------------------
-- 2. CREATE civix.investigative_finding — Relational finding table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS civix.investigative_finding (
    finding_id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id               UUID        NOT NULL REFERENCES civix.investigative_lead(lead_id) ON DELETE CASCADE,
    finding_type          TEXT        NOT NULL,
    -- e.g. SHARED_PHONE, SHARED_FINANCIAL_ACCOUNT, EXPLICIT_ASSOCIATION,
    --      TEMPORAL_COLOCATION, REPEATED_COLOCATION, COMMUNICATION_LINK,
    --      IDENTITY_CANDIDATE, COMMON_ORG_MEMBER, FINANCIAL_TRANSFER,
    --      MULTI_HOP_COMMUNICATION
    subject_entity_id     UUID        NOT NULL REFERENCES civix.entity(entity_id),
    object_entity_id      UUID        NULL     REFERENCES civix.entity(entity_id),
    relationship_strength TEXT        NOT NULL DEFAULT 'MODERATE',
    -- STRONG | MODERATE | WEAK
    key_facts             JSONB       NOT NULL DEFAULT '[]'::jsonb,
    -- Array of human-readable fact strings derived deterministically
    evidence_ids          UUID[]      NOT NULL DEFAULT '{}'::uuid[],
    -- UUIDs of assertions/events that support this finding
    path_description      TEXT        NULL,
    -- Human-readable path description e.g. "Vikram → PhoneNumber X → Neha"
    hop_count             INT         NOT NULL DEFAULT 1,
    -- 1 = direct, 2+ = multi-hop
    matching_rule_id      TEXT        NULL,
    -- Deterministic rule identifier e.g. FINDING-07, RULE_01_NAME_PHONE
    date_range_start      TIMESTAMPTZ NULL,
    date_range_end        TIMESTAMPTZ NULL,
    suppressed            BOOLEAN     NOT NULL DEFAULT FALSE,
    -- TRUE = finding was computed but suppressed (common-name defense etc.)
    suppression_reason    TEXT        NULL,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_finding_relationship_strength
        CHECK (relationship_strength IN ('STRONG', 'MODERATE', 'WEAK')),
    CONSTRAINT chk_finding_hop_count
        CHECK (hop_count >= 1 AND hop_count <= 5)
);

COMMENT ON TABLE civix.investigative_finding IS
    'Relational store of deterministic findings that support an investigative_lead. Each finding is independently source-backed. C3.';
COMMENT ON COLUMN civix.investigative_finding.evidence_ids IS
    'UUIDs of civix.assertion or civix.event rows that provide the deterministic basis. Full provenance chain: finding → assertion → extraction → observation → evidence_instance → source.';
COMMENT ON COLUMN civix.investigative_finding.suppressed IS
    'TRUE if this finding was computed but suppressed (e.g. common-name defense, public org defense). Retained for audit purposes.';

-- ---------------------------------------------------------------------------
-- 3. Indexes for C3 query patterns
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_lead_explanation_status
    ON civix.investigative_lead(explanation_status);

CREATE INDEX IF NOT EXISTS idx_lead_feature_version
    ON civix.investigative_lead(feature_vector_version);

CREATE INDEX IF NOT EXISTS idx_finding_lead
    ON civix.investigative_finding(lead_id);

CREATE INDEX IF NOT EXISTS idx_finding_subject
    ON civix.investigative_finding(subject_entity_id);

CREATE INDEX IF NOT EXISTS idx_finding_object
    ON civix.investigative_finding(object_entity_id);

CREATE INDEX IF NOT EXISTS idx_finding_type
    ON civix.investigative_finding(finding_type);

-- ---------------------------------------------------------------------------
-- 4. Update outbox trigger payload for investigative_lead
--    Include the C3 columns (explanation_status, feature_vector_version)
--    in the outbox payload so the CDC worker and Neo4j projection are aware.
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
        -- C3: Include explanation_status and feature_vector_version in payload
        v_payload := jsonb_build_object(
            'lead_id', NEW.lead_id,
            'case_id', NEW.case_id,
            'target_entity_id', NEW.target_entity_id,
            'hypothesis_id', NEW.hypothesis_id,
            'lead_text', NEW.lead_text,
            'priority', NEW.priority,
            'status', NEW.status,
            'ai_confidence', NEW.ai_confidence,
            'explanation_status', NEW.explanation_status,
            'feature_vector_version', NEW.feature_vector_version,
            'finding_count', jsonb_array_length(COALESCE(NEW.deterministic_findings, '[]'::jsonb))
        );

    ELSIF TG_TABLE_NAME = 'event_participant' THEN
        v_entity_id := NEW.participant_id;
        v_entity_type := 'event_participant';
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

-- Re-create the trigger to fire on the new columns as well
DROP TRIGGER IF EXISTS trg_lead_upsert_outbox ON civix.investigative_lead;

CREATE TRIGGER trg_lead_upsert_outbox
AFTER INSERT OR UPDATE OF
    case_id, status, priority, target_entity_id, hypothesis_id,
    explanation_status, feature_vector_version, ai_confidence
ON civix.investigative_lead
FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox();

-- ---------------------------------------------------------------------------
-- 5. Verification query (non-destructive)
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    col_count INT;
    tbl_exists BOOLEAN;
BEGIN
    -- Verify all 4 new columns on investigative_lead exist
    SELECT COUNT(*) INTO col_count
    FROM information_schema.columns
    WHERE table_schema = 'civix'
      AND table_name   = 'investigative_lead'
      AND column_name  IN ('feature_vector_version','deterministic_findings',
                           'explanation','explanation_status');
    IF col_count != 4 THEN
        RAISE EXCEPTION 'Migration 029 FAILED: Expected 4 new columns on investigative_lead, found %', col_count;
    END IF;

    -- Verify investigative_finding table exists
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'civix'
          AND table_name   = 'investigative_finding'
    ) INTO tbl_exists;
    IF NOT tbl_exists THEN
        RAISE EXCEPTION 'Migration 029 FAILED: investigative_finding table not created';
    END IF;

    RAISE NOTICE 'Migration 029 VERIFIED OK: 4 new columns + investigative_finding table';
END;
$$;

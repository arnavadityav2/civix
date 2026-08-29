-- =============================================================================
-- CIVIX Platform — Migration 002: Users, Access & Synthetic Data Control
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 03 (Users & Access)
--            docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 15 (Synthetic Data Control)
--            ADR-010: No password storage in civix_user
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.civix_user
-- Authority: Schema Bible §Migration 03
-- ADR-010: Authentication secrets NEVER stored here. Use external auth provider.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.civix_user (
    user_id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    external_auth_id TEXT         NOT NULL UNIQUE,  -- Reference to Keycloak/auth provider. No passwords.
    username         TEXT         NOT NULL UNIQUE,
    display_name     TEXT         NOT NULL,
    role             civix.civix_role_enum NOT NULL,
    clearance_level  civix.clearance_enum  NOT NULL DEFAULT 'UNCLASSIFIED',
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    department       TEXT         NULL,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_login_at    TIMESTAMPTZ  NULL
);
-- INVARIANT: No password_hash column — authentication is external (ADR-010)
-- INVARIANT: role = maximum global capability; per-case permissions in case_access

COMMENT ON TABLE civix.civix_user IS
    'System users. Authentication is external (auth provider). No passwords stored here. ADR-010.';

-- ---------------------------------------------------------------------------
-- Synthetic Data Control Tables
-- Authority: Schema Bible §Migration 15
-- These tables live early in migration order because generation_run_id
-- is referenced as FK by almost every operational table.
-- ---------------------------------------------------------------------------

CREATE TABLE civix.dataset (
    dataset_id           UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    name                 TEXT          NOT NULL UNIQUE,
    dataset_type         civix.dataset_type_enum NOT NULL,
    version              TEXT          NULL,
    is_production_isolated BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT now()
);

COMMENT ON TABLE civix.dataset IS
    'Logical grouping of synthetic or production data. GOLDEN_WORLD is the Phase 3 validation dataset.';

CREATE TABLE civix.scenario (
    scenario_id     UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id      UUID    NOT NULL REFERENCES civix.dataset(dataset_id),
    scenario_label  TEXT    NOT NULL,
    random_seed     BIGINT  NOT NULL,
    ground_truth    JSONB   NULL  -- INVARIANT (INV-14): NEVER projected to Neo4j; NEVER in ML feature extraction
);

COMMENT ON TABLE civix.scenario IS
    'A named investigative scenario within a dataset. ground_truth is for validation ONLY. INV-14.';

CREATE TABLE civix.generation_run (
    run_id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id       UUID        NULL REFERENCES civix.scenario(scenario_id),
    generator_version TEXT        NOT NULL,
    started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at       TIMESTAMPTZ NULL,
    record_counts     JSONB       NULL  -- e.g. {"persons": 55, "cdrs": 385}
);

COMMENT ON TABLE civix.generation_run IS
    'One execution of the synthetic data generator. ML pipelines MUST filter WHERE generation_run_id IS NULL to exclude synthetic rows.';

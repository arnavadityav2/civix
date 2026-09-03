-- =============================================================================
-- CIVIX Platform — Migration 021: Entity Tombstoning (ADR-033 / ADR-018)
-- Date: 2026-08-31
-- Authority: ADR-033 Entity Retrieval & Visibility
-- =============================================================================

SET search_path TO civix, public;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'visibility_status_enum') THEN
        CREATE TYPE civix.visibility_status_enum AS ENUM ('ACTIVE', 'TOMBSTONED');
    END IF;
END $$;

-- 2. Add or convert column on civix.entity
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='civix' AND table_name='entity' AND column_name='visibility_status') THEN
        ALTER TABLE civix.entity ADD COLUMN visibility_status civix.visibility_status_enum NOT NULL DEFAULT 'ACTIVE';
    END IF;
END $$;

COMMENT ON COLUMN civix.entity.visibility_status IS 'ADR-033: Enforces logical tombstoning. Tombstoned entities are invisible via normal retrieval.';

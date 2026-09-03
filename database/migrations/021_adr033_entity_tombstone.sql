-- =============================================================================
-- CIVIX Platform — Migration 021: Entity Tombstoning (ADR-033 / ADR-018)
-- Date: 2026-08-31
-- Authority: ADR-033 Entity Retrieval & Visibility
-- =============================================================================

SET search_path TO civix, public;

-- 1. Create the visibility enum explicitly enforcing logical states
CREATE TYPE civix.visibility_status_enum AS ENUM (
    'ACTIVE',
    'TOMBSTONED'
);

-- 2. Add the missing column to civix.entity
ALTER TABLE civix.entity 
ADD COLUMN visibility_status civix.visibility_status_enum NOT NULL DEFAULT 'ACTIVE';

COMMENT ON COLUMN civix.entity.visibility_status IS 'ADR-033: Enforces logical tombstoning. Tombstoned entities are invisible via normal retrieval.';

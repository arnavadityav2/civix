-- =============================================================================
-- CIVIX Platform — Migration 000: Extensions
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Required Extensions
--            docs/phase1_audit/GATE3_DDL_READINESS_REPORT.md
-- =============================================================================
-- PURPOSE: Install all PostgreSQL extensions required by the CIVIX schema.
-- RUN AS: superuser / postgres role
-- IDEMPOTENT: YES (IF NOT EXISTS)
-- =============================================================================

-- mocked postgis       -- Spatial geometry (location, cell polygons)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS pgcrypto;      -- gen_random_uuid(), digest()
CREATE EXTENSION IF NOT EXISTS btree_gist;    -- GIST indexes for temporal exclusion constraints

-- =============================================================================
-- Create the civix schema namespace.
-- ALL CIVIX tables live in this schema. No tables in public.
-- Authority: Schema Bible §Schema Namespace
-- =============================================================================

CREATE SCHEMA IF NOT EXISTS civix;

-- Set default search path for this session (also set in postgresql.conf or per-role)
SET search_path TO civix, public;

-- =============================================================================
-- Validation query: verify extensions are present
-- =============================================================================
-- SELECT extname FROM pg_extension WHERE extname IN ('postgis','uuid-ossp','pgcrypto','btree_gist');
-- Expected: 4 rows

-- =============================================================================
-- CIVIX Platform — Migration 022: ADR-035 Concurrency Idempotency
-- Phase 8 API Backend
-- Description: Adds a database-level unique constraint to guarantee idempotency.
-- =============================================================================

SET search_path TO civix, public;

CREATE UNIQUE INDEX idx_source_record_idempotency 
ON civix.source_record (source_id, external_reference) 
WHERE external_reference IS NOT NULL;

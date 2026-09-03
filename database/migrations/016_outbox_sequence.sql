-- =============================================================================
-- CIVIX Platform — Migration 016: Outbox Sequence
-- Phase 7 Neo4j Projection
-- =============================================================================

SET search_path TO civix, public;

-- Add error_status and error_message columns for dead-lettering if they don't exist
ALTER TABLE civix.outbox ADD COLUMN IF NOT EXISTS error_status TEXT NULL;
ALTER TABLE civix.outbox ADD COLUMN IF NOT EXISTS error_message TEXT NULL;

-- 1. Add BIGSERIAL sequence (PostgreSQL automatically populates existing rows with the sequence)
ALTER TABLE civix.outbox ADD COLUMN seq_no BIGSERIAL NOT NULL UNIQUE;

-- 2. Create the sequence index to optimize the CDC worker's primary cursor
-- We only care about unprocessed rows, so a partial index is optimal
CREATE INDEX IF NOT EXISTS idx_outbox_pending_events 
ON civix.outbox (seq_no ASC) 
WHERE consumed_at IS NULL;

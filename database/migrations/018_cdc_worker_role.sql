-- =============================================================================
-- CIVIX Platform — Migration 018: CDC Worker Role
-- Phase 7 Neo4j Projection
-- =============================================================================

SET search_path TO civix, public;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'civix_cdc_worker') THEN
        CREATE ROLE civix_cdc_worker WITH LOGIN PASSWORD 'cdc_worker_pass_123';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA civix TO civix_cdc_worker;
GRANT SELECT, UPDATE ON civix.outbox TO civix_cdc_worker;
GRANT USAGE, SELECT ON SEQUENCE civix.outbox_seq_no_seq TO civix_cdc_worker;
GRANT EXECUTE ON FUNCTION civix.claim_next_outbox_event() TO civix_cdc_worker;

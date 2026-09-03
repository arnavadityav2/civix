-- =============================================================================
-- CIVIX Platform — Migration 017: Outbox Queue Function
-- Phase 7 Neo4j Projection
-- =============================================================================

SET search_path TO civix, public;

CREATE OR REPLACE FUNCTION civix.claim_next_outbox_event()
RETURNS TABLE(id UUID, entity_id UUID, action TEXT, entity_type TEXT, payload JSONB, seq_no BIGINT)
LANGUAGE plpgsql AS $$
DECLARE
    rec RECORD;
    locked_rec RECORD;
BEGIN
    FOR rec IN 
        SELECT o.id, o.entity_id
        FROM civix.outbox o
        WHERE o.consumed_at IS NULL 
        -- CRITICAL: Block the entire entity if it has a dead-lettered event
        AND NOT EXISTS (
            SELECT 1 FROM civix.outbox e 
            WHERE e.entity_id = o.entity_id 
              AND e.consumed_at IS NULL 
              AND e.error_status IS NOT NULL
        )
        ORDER BY o.seq_no ASC
    LOOP
        -- Attempt to lock only this specific row
        SELECT * INTO locked_rec 
        FROM civix.outbox 
        WHERE civix.outbox.id = rec.id 
        FOR UPDATE SKIP LOCKED;
        
        IF FOUND THEN
            -- Attempt to acquire the per-entity lock.
            IF pg_try_advisory_xact_lock(hashtext(locked_rec.entity_id::text)) THEN
                RETURN QUERY SELECT locked_rec.id, locked_rec.entity_id, locked_rec.action, locked_rec.entity_type, locked_rec.payload, locked_rec.seq_no;
                RETURN;
            END IF;
        END IF;
    END LOOP;
END;
$$;

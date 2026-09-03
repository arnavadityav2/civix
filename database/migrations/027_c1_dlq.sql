-- Migration 027: C1 DLQ implementation

ALTER TABLE civix.outbox ADD COLUMN retry_count INTEGER NOT NULL DEFAULT 0;

CREATE OR REPLACE FUNCTION civix.claim_next_outbox_event()
 RETURNS TABLE(id uuid, entity_id uuid, action text, entity_type text, payload jsonb, seq_no bigint)
 LANGUAGE plpgsql
AS $function$
DECLARE
    rec RECORD;
    locked_rec RECORD;
BEGIN
    FOR rec IN 
        SELECT o.id, o.entity_id
        FROM civix.outbox o
        WHERE o.consumed_at IS NULL 
        AND o.error_status IS DISTINCT FROM 'PERMANENT_FAILURE'
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
$function$

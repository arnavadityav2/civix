import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
conn.autocommit = True
with conn.cursor() as cur:
    cur.execute("DROP FUNCTION IF EXISTS civix.claim_next_outbox_event()")
    cur.execute("""
CREATE OR REPLACE FUNCTION civix.claim_next_outbox_event()
 RETURNS TABLE(id uuid, entity_id uuid, action text, entity_type text, payload jsonb, seq_no bigint, retry_count integer)
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
        SELECT * INTO locked_rec 
        FROM civix.outbox 
        WHERE civix.outbox.id = rec.id 
        FOR UPDATE SKIP LOCKED;
        
        IF FOUND THEN
            IF pg_try_advisory_xact_lock(hashtext(locked_rec.entity_id::text)) THEN
                RETURN QUERY SELECT locked_rec.id, locked_rec.entity_id, locked_rec.action, locked_rec.entity_type, locked_rec.payload, locked_rec.seq_no, locked_rec.retry_count;
                RETURN;
            END IF;
        END IF;
    END LOOP;
END;
$function$
""")
print("Updated claim function with retry_count.")

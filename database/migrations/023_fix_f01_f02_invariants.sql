-- 023_fix_f01_f02_invariants.sql
-- Fix F-01: Idempotency index ignores NULLs.
DROP INDEX IF EXISTS civix.idx_source_record_idempotency;

CREATE UNIQUE INDEX idx_source_record_idempotency 
ON civix.source_record 
USING btree (source_id, COALESCE(external_reference, ENCODE(raw_content_hash, 'hex')));

-- Fix F-02: Entity Physical Immutability.
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.triggers 
        WHERE trigger_schema = 'civix' 
        AND trigger_name = 'enforce_no_delete_unless_synthetic' 
        AND event_object_table = 'entity'
    ) THEN
        CREATE TRIGGER enforce_no_delete_unless_synthetic
        BEFORE DELETE ON civix.entity
        FOR EACH ROW EXECUTE FUNCTION civix.trg_entity_no_delete();
    END IF;
END $$;

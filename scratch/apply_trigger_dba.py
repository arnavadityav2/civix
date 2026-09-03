import psycopg2
import sys

DSNS = [
    "postgresql://civix_dba:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test",
    "postgresql://postgres:postgres@localhost:5433/civix_test",
    "postgresql://postgres@localhost:5433/civix_test"
]

def apply_trigger():
    for dsn in DSNS:
        try:
            with psycopg2.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
        -- CDC Trigger for identity_candidate -> CANDIDATE_FOR edge
        CREATE OR REPLACE FUNCTION civix.trg_outbox_identity_candidate()
        RETURNS TRIGGER AS $$
        DECLARE
            payload JSONB;
        BEGIN
            IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
                -- Only project active candidates
                IF NEW.is_active = TRUE THEN
                    payload := jsonb_build_object(
                        'candidate_id', NEW.candidate_id,
                        'source_identity_id', NEW.source_identity_id,
                        'proposed_person_id', NEW.proposed_person_id,
                        'matching_rule_id', NEW.matching_rule_id,
                        'deterministic_signals', NEW.deterministic_signals,
                        'is_active', NEW.is_active
                    );
                    
                    INSERT INTO civix.outbox (
                        entity_id, 
                        action, 
                        entity_type, 
                        payload
                    ) VALUES (
                        NEW.source_identity_id, -- lock on source_identity to serialize
                        'UPSERT_EDGE',
                        'identity_candidate',
                        payload
                    );
                ELSIF TG_OP = 'UPDATE' AND NEW.is_active = FALSE AND OLD.is_active = TRUE THEN
                    -- Deactivate the edge
                    payload := jsonb_build_object(
                        'candidate_id', NEW.candidate_id,
                        'source_identity_id', NEW.source_identity_id,
                        'proposed_person_id', NEW.proposed_person_id
                    );
                    
                    INSERT INTO civix.outbox (
                        entity_id, 
                        action, 
                        entity_type, 
                        payload
                    ) VALUES (
                        NEW.source_identity_id,
                        'DEACTIVATE_EDGE',
                        'identity_candidate',
                        payload
                    );
                END IF;
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
                    """)
                conn.commit()
                print(f"Trigger updated successfully with DSN: {dsn}")
                return
        except Exception as e:
            print(f"Failed with {dsn}: {e}")

if __name__ == "__main__":
    apply_trigger()

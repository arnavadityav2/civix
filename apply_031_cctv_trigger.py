import asyncio
import asyncpg
import sys

DB_CONFIGS = [
    "postgresql://postgres:postgres@localhost:5433/civix_test",
    "postgresql://postgres:@localhost:5433/civix_test",
]

sql = """
SET search_path TO civix, public;

CREATE OR REPLACE FUNCTION civix.trg_cctv_observation_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
    v_payload JSONB;
BEGIN
    v_payload := jsonb_build_object(
        'observation_id', NEW.observation_id,
        'case_id', NEW.case_id,
        'camera_id', NEW.camera_id,
        'target_vehicle_id', (SELECT target_vehicle_id FROM civix.cctv_match_candidate WHERE candidate_id = NEW.candidate_id),
        'signal_class', NEW.signal_class,
        'investigator_notes', NEW.investigator_notes,
        'reviewed_at', NEW.reviewed_at
    );

    INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
    VALUES (NEW.observation_id, 'CCTV_OBSERVATION_CREATED', 'cctv_observation', v_payload);
    
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_cctv_observation_outbox ON civix.cctv_observation;
CREATE TRIGGER trg_cctv_observation_outbox 
AFTER INSERT OR UPDATE ON civix.cctv_observation 
FOR EACH ROW EXECUTE FUNCTION civix.trg_cctv_observation_outbox();
"""

async def apply(dsn: str):
    print(f"Connecting to: {dsn.split('@')[-1]}")
    conn = await asyncpg.connect(dsn, server_settings={'search_path': 'civix,public'})
    try:
        await conn.execute(sql)
        print("CCTV trigger created successfully!")
    finally:
        await conn.close()

async def main():
    for dsn in DB_CONFIGS:
        try:
            await apply(dsn)
            return
        except Exception as e:
            print(e)
            continue
    sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import asyncpg
from civix_api.config import settings

async def apply_migration():
    db_url = settings.civix_database_url.replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(db_url)
    with open("database/migrations/015_outbox_node_triggers.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    
    # Split the script into statements manually if asyncpg isn't executing them
    # Actually, asyncpg execute should execute everything. But let's verify.
    
    # To be safe, we will just execute the whole file inside a transaction block or 
    # use the underlying postgres protocol if it is failing quietly.
    # We can also just run it via SQLAlchemy which splits things better sometimes?
    # No, sqlalchemy complained about prepared statements.
    
    # Let's split by double semicolon or just execute as one big script string if we wrap it in a DO block.
    # No, we can't create functions in a DO block.
    
    # We will split it simply:
    statements = [
        "SET search_path TO civix, public;",
        """CREATE OR REPLACE FUNCTION civix.trg_upsert_node_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
DECLARE
    v_entity_type TEXT;
    v_entity_id UUID;
    v_payload JSONB;
BEGIN
    IF TG_TABLE_NAME = 'investigative_case' THEN
        v_entity_id := NEW.case_id;
        v_entity_type := 'investigative_case';
        v_payload := jsonb_build_object(
            'case_id', NEW.case_id,
            'case_number', NEW.case_number,
            'title', NEW.title,
            'case_type', NEW.case_type,
            'status', NEW.status,
            'priority', NEW.priority
        );
    ELSIF TG_TABLE_NAME = 'fir' THEN
        v_entity_id := NEW.fir_id;
        v_entity_type := 'fir';
        v_payload := jsonb_build_object(
            'fir_id', NEW.fir_id,
            'case_id', NEW.case_id,
            'fir_number', NEW.fir_number,
            'police_station', NEW.police_station
        );
    ELSIF TG_TABLE_NAME = 'person' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'person';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'display_name', NEW.display_name,
            'date_of_birth', NEW.date_of_birth,
            'gender', NEW.gender,
            'nationality', NEW.nationality
        );
    ELSIF TG_TABLE_NAME = 'phone_number' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'phone_number';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'msisdn', NEW.msisdn,
            'country_code', NEW.country_code
        );
    ELSIF TG_TABLE_NAME = 'device' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'device';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'imei', NEW.imei,
            'mac_address', NEW.mac_address,
            'device_type', NEW.device_type,
            'manufacturer', NEW.manufacturer,
            'model', NEW.model
        );
    ELSIF TG_TABLE_NAME = 'vehicle' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'vehicle';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'registration_number', NEW.registration_number,
            'vin', NEW.vin,
            'vehicle_type', NEW.vehicle_type
        );
    ELSIF TG_TABLE_NAME = 'property' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'property';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'property_ref', NEW.property_ref,
            'property_type', NEW.property_type
        );
    ELSIF TG_TABLE_NAME = 'financial_account' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'financial_account';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'masked_number', NEW.masked_number,
            'account_type', NEW.account_type,
            'bank_name', NEW.bank_name
        );
    ELSIF TG_TABLE_NAME = 'organization' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'organization';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'legal_name', NEW.legal_name,
            'org_type', NEW.org_type
        );
    ELSIF TG_TABLE_NAME = 'network' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'network';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'network_name', NEW.network_name,
            'network_type', NEW.network_type
        );
    ELSIF TG_TABLE_NAME = 'location' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'location';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'location_name', NEW.location_name,
            'location_type', NEW.location_type
        );
    ELSIF TG_TABLE_NAME = 'source_identity' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'source_identity';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'raw_identifier', NEW.raw_identifier,
            'identifier_type', NEW.identifier_type
        );
    ELSIF TG_TABLE_NAME = 'sim' THEN
        v_entity_id := NEW.entity_id;
        v_entity_type := 'sim';
        v_payload := jsonb_build_object(
            'entity_id', NEW.entity_id,
            'iccid', NEW.iccid,
            'imsi', NEW.imsi
        );
    END IF;

    IF v_payload IS NOT NULL THEN
        INSERT INTO civix.outbox (entity_id, action, entity_type, payload)
        VALUES (v_entity_id, 'UPSERT_NODE', v_entity_type, v_payload);
    END IF;

    RETURN NEW;
END;
$$;""",
    ]
    for tbl in [
        "person", "phone_number", "device", "vehicle", "property",
        "financial_account", "organization", "network", "location",
        "source_identity", "sim", "investigative_case", "fir"
    ]:
        statements.append(f"DROP TRIGGER IF EXISTS trg_{tbl}_upsert_outbox ON civix.{tbl};")
        statements.append(f"CREATE TRIGGER trg_{tbl}_upsert_outbox AFTER INSERT OR UPDATE ON civix.{tbl} FOR EACH ROW EXECUTE FUNCTION civix.trg_upsert_node_outbox();")
    
    for s in statements:
        await conn.execute(s)
        
    await conn.close()
    print("Migration applied successfully manually!")

if __name__ == "__main__":
    asyncio.run(apply_migration())

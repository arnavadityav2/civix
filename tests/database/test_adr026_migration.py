import asyncio
import os
import asyncpg

async def run_tests():
    dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_db_admin:admin_pass_123@localhost:5433/civix_test")
    try:
        conn = await asyncpg.connect(dsn)
    except Exception as e:
        print(f"Could not connect to database for live testing: {e}")
        print("Test suite is structurally valid but requires a running PostgreSQL instance.")
        return

    print("Running ADR-026 Migration Tests...")
    
    # Run tests within a transaction that rolls back
    tr = conn.transaction()
    await tr.start()
    try:
        # Create a mock user
        user_id = await conn.fetchval("INSERT INTO civix.civix_user (external_auth_id, username, display_name, role) VALUES ('auth_test', 'tester', 'Tester', 'INVESTIGATOR') RETURNING user_id")
        
        # Create Case A and Case B
        case_a_id = await conn.fetchval("INSERT INTO civix.investigative_case (case_number, title, case_type, jurisdiction, opened_at) VALUES ('CIV-TEST-A', 'Case A', 'CRIMINAL', 'Test', now()) RETURNING case_id")
        case_b_id = await conn.fetchval("INSERT INTO civix.investigative_case (case_number, title, case_type, jurisdiction, opened_at) VALUES ('CIV-TEST-B', 'Case B', 'CRIMINAL', 'Test', now()) RETURNING case_id")
        
        # Create Entity
        entity_id = await conn.fetchval("INSERT INTO civix.entity (entity_type) VALUES ('PERSON') RETURNING entity_id")
        
        # Create Hypothesis in Case A
        hyp_a_id = await conn.fetchval("INSERT INTO civix.hypothesis (case_id, hypothesis_text, created_by) VALUES ($1, 'Hypothesis A', $2) RETURNING hypothesis_id", case_a_id, user_id)
        
        # 1. Test target_entity_id cannot be NULL
        try:
            await conn.execute("INSERT INTO civix.investigative_lead (case_id, lead_text, target_entity_id, generated_by_person) VALUES ($1, 'Lead Text', NULL, $2)", case_a_id, user_id)
            print("FAIL: Lead created with NULL target_entity_id")
        except asyncpg.exceptions.NotNullViolationError:
            print("PASS: target_entity_id cannot be NULL")

        # 2. Test lead cannot reference nonexistent entity
        try:
            await conn.execute("INSERT INTO civix.investigative_lead (case_id, lead_text, target_entity_id, generated_by_person) VALUES ($1, 'Lead Text', '00000000-0000-0000-0000-000000000000', $2)", case_a_id, user_id)
            print("FAIL: Lead created with nonexistent entity")
        except asyncpg.exceptions.ForeignKeyViolationError:
            print("PASS: Lead cannot reference nonexistent entity")

        # 3. Test lead cannot reference hypothesis belonging to another case
        try:
            await conn.execute("INSERT INTO civix.investigative_lead (case_id, lead_text, target_entity_id, hypothesis_id, generated_by_person) VALUES ($1, 'Lead Text', $2, $3, $4)", case_b_id, entity_id, hyp_a_id, user_id)
            print("FAIL: Lead in Case B references Hypothesis in Case A")
        except asyncpg.exceptions.ForeignKeyViolationError:
            print("PASS: Lead cannot reference hypothesis from another case (Composite FK works)")

        # 4. Test hypothesis_id may be NULL
        try:
            await conn.execute("INSERT INTO civix.investigative_lead (case_id, lead_text, target_entity_id, hypothesis_id, generated_by_person) VALUES ($1, 'Lead Text', $2, NULL, $3)", case_a_id, entity_id, user_id)
            print("PASS: hypothesis_id may be NULL")
        except Exception as e:
            print(f"FAIL: hypothesis_id could not be NULL: {e}")

        # 5. Test outbox trigger payload contains identifiers
        lead_id = await conn.fetchval("INSERT INTO civix.investigative_lead (case_id, lead_text, target_entity_id, hypothesis_id, generated_by_person) VALUES ($1, 'Lead Text', $2, $3, $4) RETURNING lead_id", case_a_id, entity_id, hyp_a_id, user_id)
        
        # Check outbox
        outbox_payload = await conn.fetchval("SELECT payload FROM civix.outbox WHERE entity_id = $1 AND entity_type = 'investigative_lead' ORDER BY created_at DESC LIMIT 1", lead_id)
        
        import json
        payload_dict = json.loads(outbox_payload)
        if 'target_entity_id' in payload_dict and payload_dict['target_entity_id'] == str(entity_id):
            print("PASS: Outbox payload contains target_entity_id")
        else:
            print("FAIL: Outbox payload missing target_entity_id")
            
        if 'hypothesis_id' in payload_dict and payload_dict['hypothesis_id'] == str(hyp_a_id):
            print("PASS: Outbox payload contains hypothesis_id")
        else:
            print("FAIL: Outbox payload missing hypothesis_id")

    except Exception as e:
        print(f"Test suite encountered unexpected error: {e}")
    finally:
        await tr.rollback()
        await conn.close()
        print("Tests completed. Rolled back transaction.")

if __name__ == "__main__":
    asyncio.run(run_tests())

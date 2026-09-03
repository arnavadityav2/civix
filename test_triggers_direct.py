import asyncio
import asyncpg
from civix_api.config import settings

async def run_tests():
    db_url = settings.civix_database_url.replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(db_url)
    
    try:
        async with conn.transaction():
            import uuid
            uid = uuid.uuid4().hex[:8]
            # Create a user
            user_id = await conn.fetchval(f"""
                INSERT INTO civix.civix_user (external_auth_id, username, display_name, role)
                VALUES ('auth-test-{uid}', 'testuser{uid}', 'Test User', 'INVESTIGATOR')
                RETURNING user_id;
            """)
            
            await conn.execute("SELECT set_config('app.current_user_id', $1, false);", str(user_id))
            
            # TEST 1: Person Upsert
            entity_id = await conn.fetchval("""
                INSERT INTO civix.entity (entity_type, created_by) 
                VALUES ('PERSON', $1) RETURNING entity_id;
            """, user_id)
            
            await conn.execute("""
                INSERT INTO civix.person (entity_id, display_name, gender)
                VALUES ($1, 'John Doe Test', 'MALE');
            """, entity_id)
            
            events = await conn.fetch("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = $1 ORDER BY created_at ASC", entity_id)
            assert len(events) == 1
            assert events[0]['action'] == 'UPSERT_NODE'
            assert events[0]['entity_type'] == 'person'
            
            payload = events[0]['payload']
            import json
            payload = json.loads(payload) if isinstance(payload, str) else payload
            assert payload['display_name'] == 'John Doe Test'
            assert payload['gender'] == 'MALE'
            assert 'notes' not in payload or payload['notes'] is None
            
            print("TEST 1 (Person INSERT) - PASSED")
            
            await conn.execute("UPDATE civix.person SET display_name = 'Johnathan Doe' WHERE entity_id = $1", entity_id)
            
            events2 = await conn.fetch("SELECT action, payload FROM civix.outbox WHERE entity_id = $1 ORDER BY created_at ASC", entity_id)
            assert len(events2) == 2
            assert events2[1]['action'] == 'UPSERT_NODE'
            payload2 = json.loads(events2[1]['payload']) if isinstance(events2[1]['payload'], str) else events2[1]['payload']
            assert payload2['display_name'] == 'Johnathan Doe'
            
            print("TEST 2 (Person UPDATE) - PASSED")
            
            # TEST 3: Case Upsert
            case_id = await conn.fetchval("""
                INSERT INTO civix.investigative_case (case_number, title, case_type, jurisdiction) 
                VALUES ('CIV-TEST', 'Test Case', 'FINANCIAL', 'Delhi') RETURNING case_id;
            """)
            
            events3 = await conn.fetch("SELECT action, entity_type, payload FROM civix.outbox WHERE entity_id = $1", case_id)
            assert len(events3) == 1
            assert events3[0]['action'] == 'UPSERT_NODE'
            assert events3[0]['entity_type'] == 'investigative_case'
            
            print("TEST 3 (Case INSERT) - PASSED")
            
            raise Exception("ROLLBACK_ON_PURPOSE")
    except Exception as e:
        if str(e) == "ROLLBACK_ON_PURPOSE":
            print("All tests passed, rolled back successfully.")
        else:
            raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_tests())

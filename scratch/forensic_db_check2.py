import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = 'postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test'

async def main():
    e = create_async_engine(DB_URL)
    async with e.begin() as conn:
        
        # 1. Entity table has no delete trigger - what does source.source_type vs agency_type look like?
        # The adversarial test uses: INSERT INTO civix.source (..., source_type=..., reliability=...)
        # But the actual table has agency_type and reliability_score
        # This is the ACTUAL FAILURE CAUSE for the adversarial test
        
        # 2. Check the RLS variable name - migration uses 'app.current_user_id'
        # but the API sets 'civix.current_user_id'
        res = await conn.execute(text(
            "SELECT prosrc FROM pg_proc WHERE proname = 'get_accessible_case_ids'"
        ))
        row = res.first()
        print("get_accessible_case_ids body:")
        print(row[0] if row else "NOT FOUND")
        
        # 3. What variable does the RLS policy actually use for investigative_case?
        res = await conn.execute(text(
            "SELECT policyname, qual FROM pg_policies WHERE schemaname='civix' AND tablename='investigative_case'"
        ))
        for r in res.fetchall():
            print(f"\nPolicy {r[0]}:")
            print(r[1])
        
        # 4. Check the case_entity_role policy
        res = await conn.execute(text(
            "SELECT policyname, qual FROM pg_policies WHERE schemaname='civix' AND tablename='case_entity_role'"
        ))
        for r in res.fetchall():
            print(f"\ncase_entity_role policy {r[0]}:")
            print(r[1])
        
        # 5. Entity delete protection?
        res = await conn.execute(text(
            "SELECT trigger_name, event_manipulation FROM information_schema.triggers "
            "WHERE event_object_schema='civix' AND event_object_table='entity'"
        ))
        trigs = r.fetchall() if (r := res) else []
        print(f"\nentity triggers: {[(r[0], r[1]) for r in res.fetchall()]}")
        
        # 6. Can we physically delete an entity?
        # Test: try to insert and delete an entity
        try:
            await conn.execute(text(
                "INSERT INTO civix.entity (entity_type, visibility_status) VALUES ('PERSON', 'ACTIVE')"
            ))
            res2 = await conn.execute(text("SELECT entity_id FROM civix.entity ORDER BY created_at DESC LIMIT 1"))
            eid = res2.scalar()
            print(f"\nInserted entity: {eid}")
            try:
                await conn.execute(text(f"DELETE FROM civix.entity WHERE entity_id = '{eid}'"))
                print("WARNING: DELETE on civix.entity SUCCEEDED - no physical delete protection!")
            except Exception as de:
                print(f"DELETE blocked (expected): {type(de).__name__}: {str(de)[:200]}")
        except Exception as ex:
            print(f"Could not test entity delete: {ex}")
        
    await e.dispose()

asyncio.run(main())

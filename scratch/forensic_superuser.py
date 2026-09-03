import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = 'postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test'

async def main():
    e = create_async_engine(DB_URL)
    async with e.begin() as conn:
        
        # 1. All RLS policies 
        res = await conn.execute(text(
            "SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname='civix' ORDER BY tablename"
        ))
        print("ALL RLS POLICIES:")
        for r in res.fetchall():
            print(f"  {r[0]}.{r[1]} ({r[2]})")
        
        # 2. Tables WITH RLS
        res = await conn.execute(text(
            "SELECT relname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='civix' AND c.relkind='r' AND c.relrowsecurity=true ORDER BY relname"
        ))
        print("\nTABLES WITH RLS ENABLED:")
        for r in res.fetchall():
            print(f"  {r[0]}")
        
        # 3. Tables WITHOUT RLS
        res = await conn.execute(text(
            "SELECT relname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='civix' AND c.relkind='r' AND c.relrowsecurity=false ORDER BY relname"
        ))
        print("\nTABLES WITHOUT RLS:")
        for r in res.fetchall():
            print(f"  {r[0]}")
    
    async with e.begin() as conn:
        # 4. NULL ext_ref check
        res = await conn.execute(text(
            "SELECT count(*) FROM civix.source_record WHERE external_reference IS NULL"
        ))
        null_count = res.scalar()
        print(f"\nSource records with NULL external_reference: {null_count}")
    
    async with e.begin() as conn:
        # 5. civix_api grants on entity
        res = await conn.execute(text(
            "SELECT privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee='civix_api' AND table_schema='civix' AND table_name='entity'"
        ))
        print(f"\ncivix_api grants on entity: {[r[0] for r in res.fetchall()]}")
    
    async with e.begin() as conn:
        # 6. Test: entity physical delete protection (using postgres superuser)
        try:
            await conn.execute(text(
                "INSERT INTO civix.entity (entity_type, visibility_status) VALUES ('PERSON', 'ACTIVE')"
            ))
        except Exception as ex:
            print(f"INSERT entity failed: {ex}")
    
    async with e.begin() as conn:
        res = await conn.execute(text(
            "SELECT entity_id FROM civix.entity ORDER BY created_at DESC LIMIT 1"
        ))
        eid = res.scalar()
        print(f"Last entity: {eid}")
        if eid:
            try:
                await conn.execute(text(f"DELETE FROM civix.entity WHERE entity_id = '{eid}'"))
                print("WARNING: DELETE on entity SUCCEEDED as postgres superuser - only app-role blocked?")
            except Exception as de:
                print(f"DELETE blocked: {str(de)[:300]}")
    
    async with e.begin() as conn:
        # 7. Check enforce_no_delete_unless_synthetic on entity
        res = await conn.execute(text(
            "SELECT trigger_name FROM information_schema.triggers "
            "WHERE event_object_schema='civix' AND event_object_table='entity'"
        ))
        trigs = [r[0] for r in res.fetchall()]
        print(f"\nEntity triggers: {trigs}")
        
        # 8. Check source_identity columns
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='source_identity' ORDER BY ordinal_position"
        ))
        print(f"source_identity cols: {[r[0] for r in res.fetchall()]}")
    
    await e.dispose()

asyncio.run(main())

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = 'postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test'

async def main():
    e = create_async_engine(DB_URL)
    async with e.begin() as conn:
        
        # 1. What RLS policies actually exist on what tables?
        res = await conn.execute(text(
            "SELECT tablename, policyname, cmd FROM pg_policies WHERE schemaname='civix' ORDER BY tablename"
        ))
        print("ALL RLS POLICIES:")
        for r in res.fetchall():
            print(f"  {r[0]}.{r[1]} ({r[2]})")
        
        # 2. What tables have RLS ENABLED?
        res = await conn.execute(text(
            "SELECT relname, relrowsecurity FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='civix' AND c.relkind='r' AND c.relrowsecurity=true ORDER BY relname"
        ))
        print("\nTABLES WITH RLS ENABLED:")
        for r in res.fetchall():
            print(f"  {r[0]}")
        
        # 3. What tables do NOT have RLS but should be considered sensitive?
        res = await conn.execute(text(
            "SELECT relname FROM pg_class c "
            "JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='civix' AND c.relkind='r' AND c.relrowsecurity=false ORDER BY relname"
        ))
        print("\nTABLES WITHOUT RLS:")
        for r in res.fetchall():
            print(f"  {r[0]}")
        
        # 4. Check civix_api role grants
        res = await conn.execute(text(
            "SELECT grantee, table_name, privilege_type FROM information_schema.role_table_grants "
            "WHERE grantee='civix_api' AND table_schema='civix' ORDER BY table_name, privilege_type"
        ))
        print("\nCIVIX_API GRANTS:")
        for r in res.fetchall():
            print(f"  {r[1]}: {r[2]}")
        
        # 5. Check migration table or alembic_version
        try:
            res = await conn.execute(text(
                "SELECT * FROM civix.migration_history ORDER BY applied_at DESC LIMIT 10"
            ))
            print("\nMIGRATION HISTORY:")
            for r in res.fetchall():
                print(f"  {r}")
        except Exception:
            try:
                res = await conn.execute(text("SELECT version_num FROM alembic_version"))
                print("\nAlembic version:", res.scalar())
            except Exception:
                print("\nNo migration tracking table found")
        
        # 6. Check concurrent idempotency: what happens when ext_ref is NULL
        res = await conn.execute(text(
            "SELECT count(*) FROM civix.source_record WHERE external_reference IS NULL"
        ))
        null_count = res.scalar()
        print(f"\nSource records with NULL external_reference: {null_count}")
        
        # Check for potential duplicate source records (null ref)
        res = await conn.execute(text(
            "SELECT source_id, raw_content_hash, count(*) as cnt "
            "FROM civix.source_record WHERE external_reference IS NULL "
            "GROUP BY source_id, raw_content_hash HAVING count(*) > 1"
        ))
        dupes = res.fetchall()
        print(f"Duplicate NULL source records (same source+hash): {len(dupes)}")
        
    await e.dispose()

asyncio.run(main())

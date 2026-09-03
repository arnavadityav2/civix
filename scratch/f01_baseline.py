import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = 'postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test'

async def main():
    e = create_async_engine(DB_URL)
    
    # Check pg_trigger filtering our own triggers vs FK constraint triggers
    async with e.begin() as conn:
        res = await conn.execute(text("""
            SELECT tgname, tgenabled
            FROM pg_trigger 
            WHERE tgrelid = 'civix.entity'::regclass
            AND tgname NOT LIKE 'RI_Constraint%'
            ORDER BY tgname
        """))
        rows = res.fetchall()
        print(f"Non-FK entity triggers: {len(rows)}")
        for r in rows:
            print(f"  {r[0]} | enabled_char={r[1]}")
    
    # Check function
    async with e.begin() as conn:
        res = await conn.execute(text("""
            SELECT proname FROM pg_proc 
            WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix')
            AND proname = 'trg_entity_no_delete'
        """))
        row = res.first()
        print(f"\nFunction trg_entity_no_delete: {'EXISTS' if row else 'MISSING'}")
    
    # Attempt DELETE with rollback
    async with e.connect() as conn:
        await conn.execute(text("BEGIN"))
        try:
            await conn.execute(text(
                "INSERT INTO civix.entity (entity_type, visibility_status) VALUES ('PERSON', 'ACTIVE')"
            ))
            res = await conn.execute(text(
                "SELECT entity_id FROM civix.entity ORDER BY created_at DESC LIMIT 1"
            ))
            eid = res.scalar()
            print(f"\nTest entity: {eid}")
            
            try:
                await conn.execute(text(f"DELETE FROM civix.entity WHERE entity_id = '{eid}'"))
                res2 = await conn.execute(text(f"SELECT COUNT(*) FROM civix.entity WHERE entity_id = '{eid}'"))
                count = res2.scalar()
                if count == 0:
                    print("VULNERABILITY CONFIRMED: DELETE succeeded — F-01 REPRODUCED")
                else:
                    print("DELETE returned OK but row still present")
            except Exception as dex:
                print(f"DELETE BLOCKED — F-01 NOT REPRODUCED")
                print(f"  Exception type: {type(dex).__name__}")
                print(f"  Message (first 300 chars): {str(dex)[:300]}")
        finally:
            await conn.execute(text("ROLLBACK"))
    
    await e.dispose()

asyncio.run(main())

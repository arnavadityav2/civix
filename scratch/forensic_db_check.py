import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DB_URL = 'postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test'

async def main():
    e = create_async_engine(DB_URL)
    async with e.begin() as conn:
        # 1. Source table columns (find the correct column names)
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='source' ORDER BY ordinal_position"
        ))
        print("source cols:", [r[0] for r in res.fetchall()])
        
        # 2. Entity triggers (check immutability)
        res = await conn.execute(text(
            "SELECT trigger_name, event_manipulation FROM information_schema.triggers "
            "WHERE event_object_schema='civix' AND event_object_table='entity'"
        ))
        print("entity triggers:", [(r[0], r[1]) for r in res.fetchall()])
        
        # 3. Source_record trigger (outbox)
        res = await conn.execute(text(
            "SELECT trigger_name, event_manipulation FROM information_schema.triggers "
            "WHERE event_object_schema='civix' AND event_object_table='source_record'"
        ))
        print("source_record triggers:", [(r[0], r[1]) for r in res.fetchall()])
        
        # 4. Check outbox table
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='outbox' ORDER BY ordinal_position"
        ))
        print("outbox cols:", [r[0] for r in res.fetchall()])
        
        # 5. Check all triggers in civix schema
        res = await conn.execute(text(
            "SELECT event_object_table, trigger_name, event_manipulation FROM information_schema.triggers "
            "WHERE event_object_schema='civix' ORDER BY event_object_table, trigger_name"
        ))
        print("ALL civix triggers:")
        for r in res.fetchall():
            print(f"  {r[0]}.{r[1]} ({r[2]})")
        
        # 6. Check RLS variable name used by helper functions
        res = await conn.execute(text(
            "SELECT prosrc FROM pg_proc WHERE proname = 'get_accessible_case_ids'"
        ))
        row = res.first()
        if row:
            print("\nget_accessible_case_ids SQL:", row[0][:500])
        
        # 7. Check entity physical delete prevention trigger
        res = await conn.execute(text(
            "SELECT prosrc FROM pg_proc WHERE proname = 'prevent_entity_delete'"
        ))
        row = res.first()
        if row:
            print("\nprevent_entity_delete SQL:", row[0][:500])
        else:
            print("\nWARNING: prevent_entity_delete function NOT FOUND")
    
    await e.dispose()

asyncio.run(main())

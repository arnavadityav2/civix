import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def detailed_schema_check():
    async with engine.connect() as conn:
        print("=== Tables containing case_id column ===")
        res = await conn.execute(text("""
            SELECT table_name, column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND column_name = 'case_id'
            ORDER BY table_name
        """))
        for r in res.fetchall():
            print(f"  {r[0]}.{r[1]}")

        print("\n=== Event table columns ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  event.{r[0]} ({r[1]})")

        print("\n=== Event location columns ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event_location'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  event_location.{r[0]} ({r[1]})")

        print("\n=== Source record columns ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'source_record'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  source_record.{r[0]} ({r[1]})")

        print("\n=== Evidence instance columns ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'evidence_instance'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  evidence_instance.{r[0]} ({r[1]})")

        print("\n=== Event participant columns ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event_participant'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  event_participant.{r[0]} ({r[1]})")

if __name__ == "__main__":
    asyncio.run(detailed_schema_check())

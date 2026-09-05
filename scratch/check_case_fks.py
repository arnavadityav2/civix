import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_fks_and_links():
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

        print("\n=== Event table columns & FKs ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event'
            ORDER BY ordinal_position
        """))
        for r in res.fetchall():
            print(f"  event.{r[0]} ({r[1]})")

        # Let's see how event is linked to case! Is it via source_record? Or event_participant? Or case_id?
        res = await conn.execute(text("""
            SELECT e.event_id, e.description, sr.case_id 
            FROM civix.event e
            LEFT JOIN civix.source_record sr ON e.source_record_id = sr.source_record_id
            LIMIT 10
        """))
        print("\n=== Sample event -> source_record -> case_id ===")
        for r in res.fetchall():
            print(r)

if __name__ == "__main__":
    asyncio.run(check_fks_and_links())

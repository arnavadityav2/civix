import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_event_counts():
    async with engine.connect() as conn:
        print("--- Event location link ---")
        res = await conn.execute(text("""
            SELECT count(distinct event_id) as distinct_events, count(distinct case_id) as distinct_cases
            FROM civix.event_location
        """))
        print("event_location counts:", res.fetchone())

        res = await conn.execute(text("""
            SELECT count(distinct e.event_id)
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
        """))
        print("events matching event_location:", res.scalar())

        res = await conn.execute(text("SELECT count(*) FROM civix.event"))
        print("Total events in DB:", res.scalar())

if __name__ == "__main__":
    asyncio.run(check_event_counts())

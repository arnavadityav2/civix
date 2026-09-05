import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def test_union_events():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            WITH combined_events AS (
                SELECT case_id, event_id FROM civix.event_location WHERE case_id IS NOT NULL
                UNION
                SELECT cer.case_id, ep.event_id 
                FROM civix.event_participant ep 
                JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
            )
            SELECT COUNT(DISTINCT case_id) as cases_with_events, COUNT(DISTINCT event_id) as total_distinct_events
            FROM combined_events
        """))
        print("Union event aggregation stats:", res.fetchone())

if __name__ == "__main__":
    asyncio.run(test_union_events())

import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_event_participant_case_links():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT count(distinct ep.event_id)
            FROM civix.event_participant ep
            JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
        """))
        print("Events with participant linked to case:", res.scalar())

        res = await conn.execute(text("""
            SELECT count(distinct ep.event_id)
            FROM civix.event_participant ep
            JOIN civix.case_entity_role cer ON ep.entity_id = cer.entity_id
            WHERE ep.event_id NOT IN (SELECT event_id FROM civix.event_location WHERE case_id IS NOT NULL)
        """))
        print("Events with participant linked to case BUT NOT in event_location:", res.scalar())

if __name__ == "__main__":
    asyncio.run(check_event_participant_case_links())

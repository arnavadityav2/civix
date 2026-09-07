import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

ASYNC_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def main():
    engine = create_async_engine(ASYNC_DB_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'"))
        cid = res.scalar()
        print("CIV-2012-001 Case ID:", cid)

        res = await conn.execute(text("""
            SELECT e.entity_type::text, COUNT(*) 
            FROM civix.case_entity_role cer 
            JOIN civix.entity e ON cer.entity_id = e.entity_id 
            WHERE cer.case_id = :cid 
            GROUP BY e.entity_type::text
        """), {'cid': cid})
        print("case_entity_role breakdown:")
        for row in res.fetchall():
            print(" ", row[0], ":", row[1])

        res = await conn.execute(text("SELECT COUNT(*) FROM civix.evidence_instance WHERE case_id = :cid"), {'cid': cid})
        print("evidence_instance count:", res.scalar())

        res = await conn.execute(text("SELECT COUNT(*) FROM civix.event_location WHERE case_id = :cid"), {'cid': cid})
        print("event_location count:", res.scalar())

if __name__ == "__main__":
    asyncio.run(main())

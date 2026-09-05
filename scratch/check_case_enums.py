import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_enums():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT DISTINCT status FROM civix.investigative_case"))
        print("Status values:", [r[0] for r in res.fetchall()])

        res = await conn.execute(text("SELECT DISTINCT priority FROM civix.investigative_case"))
        print("Priority values:", [r[0] for r in res.fetchall()])

        res = await conn.execute(text("SELECT DISTINCT case_type FROM civix.investigative_case"))
        print("Case type values:", [r[0] for r in res.fetchall()])

if __name__ == "__main__":
    asyncio.run(check_enums())

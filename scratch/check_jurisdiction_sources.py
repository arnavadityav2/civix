import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_jurisdiction_sources():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT 
                c.case_number, 
                c.jurisdiction as case_jurisdiction, 
                f.police_station as fir_police_station, 
                f.district as fir_district
            FROM civix.investigative_case c
            LEFT JOIN civix.fir f ON c.case_id = f.case_id
            LIMIT 15
        """))
        for r in res.fetchall():
            print(r)

if __name__ == "__main__":
    asyncio.run(check_jurisdiction_sources())

import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_links():
    async with engine.connect() as conn:
        print("--- Provenance / Hero check ---")
        # Check case numbers
        res = await conn.execute(text("""
            SELECT case_number, case_id, title 
            FROM civix.investigative_case 
            LIMIT 10
        """))
        for r in res.fetchall():
            print(r)

        # Check total cases
        res = await conn.execute(text("SELECT count(*) FROM civix.investigative_case"))
        print("Total cases count:", res.scalar())

        # Check if case_number starting with CIV- or in protected_hero_cases.json are hero cases
        res = await conn.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE case_number LIKE 'CIV-%') as civ_count,
                COUNT(*) FILTER (WHERE case_number LIKE 'SYN-%') as syn_count,
                COUNT(*) as total
            FROM civix.investigative_case
        """))
        print("Case number patterns:", res.fetchone())

        # Check FIR link for police station / jurisdiction
        res = await conn.execute(text("""
            SELECT f.case_id, f.police_station, f.district
            FROM civix.fir f
            LIMIT 5
        """))
        print("FIR sample:", res.fetchall())

        # Check event linkage to case
        # How is event linked to case? Let's check event table and any case_event or event_case linking table
        res = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'civix' AND table_name LIKE '%event%'
        """))
        print("Event tables:", [r[0] for r in res.fetchall()])

        res = await conn.execute(text("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'civix'
        """))
        print("All civix tables:", [r[0] for r in res.fetchall()])

if __name__ == "__main__":
    asyncio.run(check_links())

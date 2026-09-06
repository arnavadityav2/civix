import asyncio
import sys
sys.path.append('.')

from sqlalchemy import text
from civix_api.database import engine

async def cleanup():
    async with engine.begin() as conn:
        await conn.execute(text("""
            DELETE FROM civix.evidence_instance 
            WHERE case_id IN (SELECT case_id FROM civix.investigative_case WHERE case_number LIKE 'TEST-%')
        """))
        await conn.execute(text("""
            DELETE FROM civix.case_access 
            WHERE case_id IN (SELECT case_id FROM civix.investigative_case WHERE case_number LIKE 'TEST-%')
        """))
        res = await conn.execute(text("""
            DELETE FROM civix.investigative_case 
            WHERE case_number LIKE 'TEST-%'
        """))
        print("Cleaned up test cases.")

if __name__ == "__main__":
    asyncio.run(cleanup())

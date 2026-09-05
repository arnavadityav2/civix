import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_evidence():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM civix.evidence_instance"))
        print("Total evidence_instance:", res.scalar())
        
        res = await conn.execute(text("SELECT count(*) FROM civix.evidence_artifact"))
        print("Total evidence_artifact:", res.scalar())

        res = await conn.execute(text("""
            SELECT case_id, count(*) 
            FROM civix.evidence_instance 
            GROUP BY case_id 
            ORDER BY count(*) DESC 
            LIMIT 10
        """))
        print("Sample case_id evidence counts:", res.fetchall())

if __name__ == "__main__":
    asyncio.run(check_evidence())

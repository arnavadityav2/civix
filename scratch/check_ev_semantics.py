import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check_evidence_semantics():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT 
                case_id, 
                COUNT(DISTINCT instance_id) as instance_cnt,
                COUNT(DISTINCT artifact_id) as artifact_cnt
            FROM civix.evidence_instance
            GROUP BY case_id
            HAVING COUNT(DISTINCT instance_id) != COUNT(DISTINCT artifact_id)
        """))
        diffs = res.fetchall()
        print("Cases where instance_cnt != artifact_cnt:", len(diffs))

if __name__ == "__main__":
    asyncio.run(check_evidence_semantics())

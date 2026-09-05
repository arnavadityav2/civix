import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def check():
    async with engine.connect() as conn:
        tables = [
            'investigative_case', 
            'case_entity_role', 
            'entity', 
            'event', 
            'evidence_instance', 
            'evidence_artifact', 
            'investigative_lead', 
            'fir', 
            'police_station'
        ]
        for t in tables:
            res = await conn.execute(text(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'civix' AND table_name = '{t}'
                ORDER BY ordinal_position
            """))
            cols = res.fetchall()
            print(f"=== {t} ({len(cols)} cols) ===")
            for c in cols:
                print(f"  {c[0]}: {c[1]}")

if __name__ == "__main__":
    asyncio.run(check())

import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"
    engine = create_async_engine(url)
    
    output = {}
    async with engine.connect() as conn:
        for table in ['person', 'vehicle', 'case_entity_role', 'evidence_instance', 'assertion', 'event', 'investigative_finding']:
            res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = '{table}'"))
            output[table] = [r[0] for r in res.fetchall()]
            
    with open("scratch/db_schema.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

if __name__ == "__main__":
    asyncio.run(main())

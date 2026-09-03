import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test")
    
    statements = [
        "ALTER TABLE civix.hypothesis DROP CONSTRAINT IF EXISTS uq_hypothesis_case",
        "ALTER TABLE civix.investigative_lead DROP CONSTRAINT IF EXISTS fk_lead_hypothesis_case",
        "ALTER TABLE civix.hypothesis ADD CONSTRAINT uq_hypothesis_case UNIQUE (hypothesis_id, case_id)",
        "ALTER TABLE civix.investigative_lead ADD COLUMN IF NOT EXISTS target_entity_id UUID REFERENCES civix.entity(entity_id) ON DELETE RESTRICT",
        "ALTER TABLE civix.investigative_lead ADD COLUMN IF NOT EXISTS hypothesis_id UUID NULL",
        "ALTER TABLE civix.investigative_lead ADD CONSTRAINT fk_lead_hypothesis_case FOREIGN KEY (hypothesis_id, case_id) REFERENCES civix.hypothesis(hypothesis_id, case_id)"
    ]
    
    async with engine.begin() as conn:
        for stmt in statements:
            print(stmt)
            await conn.execute(text(stmt))
                
    print("Schema updated successfully!")

asyncio.run(main())

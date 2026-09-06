"""
CIVIX Environment Deep Audit - Phase 2
Check which database is being used and what data actually exists where.
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Try all possible DB connections
DB_CONFIGS = [
    ("civix_test", "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"),
    ("civix_demo_5432", "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5432/civix_demo"),
    ("civix_demo_5433", "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_demo"),
]

INDEXED_PERSON_IDS = [
    'f5c4a848-1c97-4b39-cc96-bb0b4775f8e3',
    '637038f4-633f-8457-6de9-b7142bc10381',
    '7bfb4b76-8bee-ccaf-10a6-009a09e6fc04',
]

async def test_db(name, url):
    try:
        engine = create_async_engine(url, connect_args={"timeout": 5})
        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case"))
            cases = res.scalar()
            res = await conn.execute(text("SELECT COUNT(*) FROM civix.person"))
            persons = res.scalar()
            res = await conn.execute(text("SELECT COUNT(*) FROM civix.case_entity_role"))
            roles = res.scalar()
            
            # Check person columns
            res = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'civix' AND table_name = 'person'"
            ))
            columns = [r[0] for r in res.fetchall()]
            
            # Check indexed persons
            ids_str = ",".join(f"'{p}'" for p in INDEXED_PERSON_IDS)
            try:
                res = await conn.execute(text(
                    f"SELECT entity_id::text, display_name FROM civix.person "
                    f"WHERE entity_id = ANY(ARRAY[{ids_str}]::uuid[])"
                ))
                indexed_found = [{"id": r[0], "name": r[1]} for r in res.fetchall()]
            except Exception as e:
                indexed_found = f"ERROR: {e}"

            # Check sample case numbers
            res = await conn.execute(text(
                "SELECT case_number, title FROM civix.investigative_case ORDER BY created_at LIMIT 5"
            ))
            sample_cases = [{"number": r[0], "title": r[1]} for r in res.fetchall()]
            
            return {
                "status": "CONNECTED",
                "cases": cases,
                "persons": persons,
                "roles": roles,
                "person_columns": columns,
                "indexed_found": indexed_found,
                "sample_cases": sample_cases
            }
    except Exception as e:
        return {"status": f"ERROR: {e}"}

async def main():
    results = {}
    for name, url in DB_CONFIGS:
        print(f"Testing {name}...")
        results[name] = await test_db(name, url)
    
    print(json.dumps(results, indent=2, default=str))
    with open("scratch/db_discovery.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

if __name__ == "__main__":
    asyncio.run(main())

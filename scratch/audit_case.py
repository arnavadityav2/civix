import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo")
    
    # Try different DSNs if the first one fails
    dsns = [
        dsn,
        "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_test",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    ]
    
    for url in dsns:
        try:
            print(f"Trying {url}")
            engine = create_async_engine(url)
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT * FROM civix.case WHERE display_id = 'CIV-2012-001'"))
                rows = result.fetchall()
                print("Found Case:", rows)
                if rows:
                    case_id = rows[0][0]
                    
                    print(f"\\n--- EVENTS FOR {case_id} ---")
                    events = await conn.execute(text(f"SELECT * FROM civix.event WHERE case_id = '{case_id}'"))
                    for e in events.fetchall(): print(e)
                    
                    print(f"\\n--- ENTITIES FOR {case_id} ---")
                    entities = await conn.execute(text(f"SELECT * FROM civix.entity WHERE case_id = '{case_id}'"))
                    for en in entities.fetchall(): print(en)
                    
                    print(f"\\n--- EVIDENCE FOR {case_id} ---")
                    evidence = await conn.execute(text(f"SELECT * FROM civix.evidence WHERE case_id = '{case_id}'"))
                    for ev in evidence.fetchall(): print(ev)
                    
                    print(f"\\n--- ASSERTIONS FOR {case_id} ---")
                    assertions = await conn.execute(text(f"SELECT * FROM civix.assertion WHERE case_id = '{case_id}'"))
                    for a in assertions.fetchall(): print(a)
                    
                break
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    rows = await conn.fetch("""
        SELECT case_id, case_number, title, created_at, updated_at
        FROM civix.investigative_case
        WHERE case_number NOT LIKE 'CIV-%' AND case_number NOT LIKE 'SYN-%'
    """)
    print(f"Non-canonical cases count: {len(rows)}")
    for r in rows:
        print(dict(r))
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Find case CIV-2012-001
    c1 = await conn.fetchrow("SELECT case_id, case_number, title, case_type, status, jurisdiction FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
    if not c1:
        print("CIV-2012-001 NOT FOUND in civix.investigative_case!")
        await conn.close()
        return

    print("=== CIV-2012-001 FOUND ===")
    print(f"ID: {c1['case_id']}")
    print(f"Number: {c1['case_number']}")
    print(f"Title: {c1['title']}")
    print(f"Jurisdiction: {c1['jurisdiction']}")

    # 2. Find a normal case to compare with
    c2 = await conn.fetchrow("SELECT case_id, case_number, title FROM civix.investigative_case WHERE case_number != 'CIV-2012-001' LIMIT 1")
    print("\n=== NORMAL CASE FOR COMPARISON ===")
    print(f"ID: {c2['case_id']}")
    print(f"Number: {c2['case_number']}")
    print(f"Title: {c2['title']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

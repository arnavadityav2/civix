import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Fetch test cases
    test_cases = await conn.fetch("""
        SELECT case_id, case_number, title, created_at, updated_at 
        FROM civix.investigative_case 
        WHERE case_number IN ('TEST-ORDER-001', '20226-055-TEST', '20226-055')
           OR title ILIKE '%test%' OR case_number ILIKE '%TEST%'
    """)
    print("=== Test Cases ===")
    for row in test_cases:
        print(dict(row))
        
    # 2. Fetch Golden Cases
    golden_cases = await conn.fetch("""
        SELECT case_id, case_number, title, created_at, updated_at
        FROM civix.investigative_case
        WHERE case_number IN ('CIV-2012-001', 'CIV-2026-009', 'CIV-2024-010')
    """)
    print("\n=== Target Top 3 Golden Cases ===")
    for row in golden_cases:
        print(dict(row))

    # 3. Fetch max last_activity_at of all golden cases
    max_activity = await conn.fetchval("""
        SELECT MAX(updated_at) FROM civix.investigative_case
    """)
    print(f"\nMax updated_at in DB: {max_activity}")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

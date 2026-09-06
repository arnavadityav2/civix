import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # Check all golden cases in investigative_case
    golden_cases = await conn.fetch("""
        SELECT case_id, case_number, title
        FROM civix.investigative_case
        WHERE case_number NOT LIKE 'SYN-%'
    """)
    print(f"Total Golden Cases in DB: {len(golden_cases)}")
    
    users = await conn.fetch("SELECT DISTINCT user_id FROM civix.case_access")
    
    for g in golden_cases:
        cid = g['case_id']
        cnum = g['case_number']
        grants = await conn.fetch("SELECT user_id, is_revoked FROM civix.case_access WHERE case_id = $1", cid)
        user_list = [str(r['user_id']) for r in grants if not r['is_revoked']]
        print(f"Case {cnum:<15} ({cid}): Granted to {len(user_list)} users: {user_list}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

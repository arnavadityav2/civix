import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
    users = await conn.fetch("SELECT user_id, role FROM civix.civix_user")
    print("Users:", users)
    cases = await conn.fetch("SELECT case_id FROM civix.investigative_case")
    print("Cases:", cases)
    access = await conn.fetch("SELECT case_id, user_id, access_level FROM civix.case_access")
    print("Access:", access)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

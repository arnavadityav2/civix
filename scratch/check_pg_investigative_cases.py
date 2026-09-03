import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="civix_test"
    )
    cases = await conn.fetch("SELECT case_id, case_number, title FROM civix.investigative_case;")
    print("PostgreSQL Investigative Cases:")
    for r in cases:
        print(dict(r))

    roles = await conn.fetch("SELECT case_id, entity_id, role, role_confidence FROM civix.case_entity_role;")
    print("\nCase Entity Roles in PG:", len(roles))
    for r in roles:
        print(dict(r))

    await conn.close()

asyncio.run(main())

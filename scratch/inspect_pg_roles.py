import asyncio
import asyncpg

async def inspect_roles():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Total count in case_entity_role
    cnt = await conn.fetchval("SELECT count(*) FROM civix.case_entity_role WHERE tx_end IS NULL")
    print(f"Total active case_entity_role rows in PG: {cnt}")

    # 2. Sample rows
    rows = await conn.fetch("""
        SELECT r.role_id, r.case_id, c.case_number, c.title, r.entity_id, r.role
        FROM civix.case_entity_role r
        JOIN civix.investigative_case c ON r.case_id = c.case_id
        WHERE r.tx_end IS NULL
        LIMIT 15
    """)
    print("\nSample active case_entity_role rows in PG:")
    for r in rows:
        print(f"  Case {r['case_number']} ({r['case_id']}) -> Entity {r['entity_id']} as {r['role']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(inspect_roles())

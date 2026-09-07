import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    rows = await conn.fetch("""
        SELECT case_id, case_number, title, status, priority, case_type, jurisdiction, investigating_unit
        FROM civix.investigative_case
        WHERE case_number NOT LIKE 'SYN-%'
        ORDER BY case_number;
    """)
    print(f"Total Golden Cases in DB: {len(rows)}")
    for r in rows:
        print(f"- {r['case_number']}: {r['title']} | Jurisdiction: {r['jurisdiction']} | Unit: {r['investigating_unit']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())

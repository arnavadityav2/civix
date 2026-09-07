import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='provenance';")
    print("Columns of civix.provenance:")
    for c in cols:
        print(f" - {c['column_name']}: {c['data_type']}")
        
    provs = await conn.fetch("SELECT * FROM civix.provenance LIMIT 10;")
    print("\nSample records in civix.provenance:")
    for p in provs:
        print(dict(p))

    golden_cases = await conn.fetch("SELECT case_id, case_number, title FROM civix.investigative_case WHERE case_number NOT LIKE 'SYN-%';")
    print(f"\nGolden Cases ({len(golden_cases)} total):")
    for gc in golden_cases:
        print(f" - {gc['case_number']}: {gc['title']} (ID: {gc['case_id']})")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

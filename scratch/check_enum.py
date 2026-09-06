import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    enums = await conn.fetch("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'case_permission_enum'")
    print("case_permission_enum values:", [e['enumlabel'] for e in enums])
    
    sample_grant = await conn.fetchrow("SELECT * FROM civix.case_access LIMIT 1")
    print("Sample grant row:", dict(sample_grant))

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    vikram_uid = '55284c17-1d58-461f-94f5-86c2a5215100'
    dev_uid = '00000000-0000-0000-0000-000000000001'
    
    all_cases = await conn.fetch("SELECT case_id FROM civix.investigative_case")
    print(f"Total cases in DB: {len(all_cases)}")
    
    async with conn.transaction():
        for uid in [vikram_uid, dev_uid]:
            for row in all_cases:
                cid = row['case_id']
                # Delete existing row if present then insert
                await conn.execute("DELETE FROM civix.case_access WHERE case_id = $1 AND user_id = $2", cid, uid)
                await conn.execute("""
                    INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by, granted_at, is_revoked)
                    VALUES (gen_random_uuid(), $1, $2, 'ADMIN'::civix.case_permission_enum, $2, NOW(), FALSE)
                """, cid, uid)
        print("Successfully granted full case access to Vikram S. and dev user!")

    cnt = await conn.fetchval("SELECT COUNT(*) FROM civix.case_access WHERE user_id = $1 AND is_revoked = FALSE", vikram_uid)
    print(f"Vikram S. new access count: {cnt}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

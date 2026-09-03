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
    user_id = "55284c17-1d58-461f-94f5-86c2a5215100"
    case_ids = [
        "19c74342-8c66-4f3b-a993-16f139a86877",
        "b281ad86-1b43-458c-b751-fc44cb467823"
    ]
    for cid in case_ids:
        await conn.execute("""
            INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
            VALUES ($1, $2, 'ADMIN', $2)
            ON CONFLICT (case_id, user_id) DO NOTHING;
        """, cid, user_id)
    print("Granted case access for user 55284c17-1d58-461f-94f5-86c2a5215100")
    await conn.close()

asyncio.run(main())

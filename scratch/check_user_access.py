import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    
    # 1. Fetch distinct user_ids in case_access
    user_rows = await conn.fetch("SELECT DISTINCT user_id FROM civix.case_access")
    print("=== User IDs in case_access ===")
    for u in user_rows:
        uid = u['user_id']
        count = await conn.fetchval("SELECT COUNT(*) FROM civix.case_access WHERE user_id = $1 AND is_revoked = FALSE", uid)
        print(f"User ID: {uid} | Access count: {count}")
        
    # 2. Check access for CIV-2012-001, CIV-2026-009, CIV-2024-010 per user_id
    flagship_ids = [
        '1346a86d-267a-a635-9d62-e34c76ecd24f', # CIV-2012-001
        'bb1a67a5-525b-48f8-f793-d60c23c514ca', # CIV-2026-009
        '980b70e5-465d-6aeb-a4fe-1c2ddfdb922d'  # CIV-2024-010
    ]
    
    print("\n=== Flagship Case Access per User ===")
    for u in user_rows:
        uid = u['user_id']
        has_access = await conn.fetch("""
            SELECT c.case_number, ca.is_revoked 
            FROM civix.case_access ca
            JOIN civix.investigative_case c ON ca.case_id = c.case_id
            WHERE ca.user_id = $1 AND ca.case_id::text = ANY($2)
        """, uid, flagship_ids)
        print(f"User ID {uid}: {[dict(r) for r in has_access]}")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

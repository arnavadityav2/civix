import asyncio
from civix_api.database import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT p.display_name, p.avatar_url, p.entity_id
            FROM civix.investigative_case c
            JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
            JOIN civix.person p ON cer.entity_id = p.entity_id
            WHERE c.case_number = 'CIV-2012-001'
        """))
        rows = res.fetchall()
        print(f"Verified {len(rows)} database person avatar URLs for CIV-2012-001:")
        for r in rows:
            print(f"  • {r[0]:<20} -> {r[1]}")

if __name__ == '__main__':
    asyncio.run(main())

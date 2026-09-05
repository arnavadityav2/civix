import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine
from scripts.hero_protection import get_protected_hero_case_ids

async def main():
    hero_ids = get_protected_hero_case_ids()
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT case_id::text, case_number, title, case_type, status, priority FROM civix.investigative_case ORDER BY case_id LIMIT 20"))
        rows = res.fetchall()
        for r in rows:
            is_hero = r[0].lower() in hero_ids
            print(f"ID: {r[0]}, Num: {r[1]}, Title: '{r[2]}', Type: {r[3]}, Hero: {is_hero}")

if __name__ == "__main__":
    asyncio.run(main())

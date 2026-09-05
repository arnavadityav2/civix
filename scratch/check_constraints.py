#!/usr/bin/env python3
"""Check investigative_lead constraints."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text("""
            SELECT constraint_name, check_clause
            FROM information_schema.check_constraints
            WHERE constraint_schema = 'civix'
            AND constraint_name LIKE '%lead%'
        """))
        print('investigative_lead constraints:')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['constraint_name']}: {m['check_clause']}")

    async with engine.connect() as conn:
        # Sample what explanation_status values exist
        r2 = await conn.execute(text("SELECT DISTINCT explanation_status FROM civix.investigative_lead LIMIT 10;"))
        print('Existing explanation_status values:')
        for row in r2.fetchall():
            print(' ', row[0])

asyncio.run(main())

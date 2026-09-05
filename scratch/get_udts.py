#!/usr/bin/env python3
"""Get enum type names for event_location columns."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT column_name, udt_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event_location' "
            "ORDER BY ordinal_position;"
        ))
        print('event_location column types:')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']}: data_type={m['data_type']} udt_name={m['udt_name']}")

    async with engine.connect() as conn:
        r2 = await conn.execute(text(
            "SELECT column_name, udt_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='location' "
            "ORDER BY ordinal_position;"
        ))
        print('location column types:')
        for row in r2.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']}: data_type={m['data_type']} udt_name={m['udt_name']}")

asyncio.run(main())

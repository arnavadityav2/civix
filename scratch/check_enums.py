#!/usr/bin/env python3
"""Check entity_type_enum values and lead/priority enum types."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT unnest(enum_range(NULL::entity_type_enum))::text as val;"))
        print('entity_type enum:')
        for row in r.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT unnest(enum_range(NULL::lead_priority_enum))::text as val;"))
        print('lead_priority enum:')
        for row in r.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT unnest(enum_range(NULL::lead_status_enum))::text as val;"))
        print('lead_status enum:')
        for row in r.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        # Get actual UDT name for investigative_lead.priority and .status
        r = await conn.execute(text(
            "SELECT column_name, udt_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='investigative_lead' ORDER BY ordinal_position;"
        ))
        print('investigative_lead column types:')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']}: {m['udt_name']}")

asyncio.run(main())

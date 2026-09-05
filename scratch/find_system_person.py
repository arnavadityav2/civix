#!/usr/bin/env python3
"""Find a valid generated_by_person UUID for lead insertion."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        # Find system entity
        r = await conn.execute(text(
            "SELECT entity_id::text, entity_type FROM civix.entity "
            "WHERE entity_id = '00000000-0000-0000-0000-000000000001'::uuid;"
        ))
        row = r.fetchone()
        if row:
            print(f'System entity: {dict(row._mapping)}')
        else:
            print('System entity not found')

    async with engine.connect() as conn:
        # Check what generated_by_person is in existing leads
        r2 = await conn.execute(text(
            "SELECT DISTINCT generated_by_person::text FROM civix.investigative_lead LIMIT 5;"
        ))
        print('Existing generated_by_person values:')
        for row in r2.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        # Check if that person is in entity table with correct type
        r3 = await conn.execute(text(
            "SELECT entity_id::text, entity_type FROM civix.entity "
            "WHERE entity_id IN ('00000000-0000-0000-0000-000000000001'::uuid, '55284c17-1d58-461f-94f5-86c2a5215100'::uuid);"
        ))
        for row in r3.fetchall():
            print(f'Entity: {dict(row._mapping)}')

asyncio.run(main())

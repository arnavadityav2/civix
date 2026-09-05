#!/usr/bin/env python3
"""Get all enum values with schema-qualified names."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

ENUM_NAMES = [
    'civix.entity_type_enum',
    'civix.lead_priority_enum',
    'civix.lead_status_enum',
    'civix.location_type_enum',
    'civix.predicate_enum',
    'civix.epistemic_status_enum',
]

async def main():
    for enum_name in ENUM_NAMES:
        try:
            async with engine.connect() as conn:
                r = await conn.execute(text(f"SELECT unnest(enum_range(NULL::{enum_name}))::text as val;"))
                vals = [row[0] for row in r.fetchall()]
                print(f'{enum_name}: {vals}')
        except Exception as e:
            print(f'{enum_name}: ERROR - {e}')

asyncio.run(main())

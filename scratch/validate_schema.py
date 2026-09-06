"""Validate case_entity_role columns"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    e = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo')
    async with e.connect() as c:
        r = await c.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='case_entity_role' ORDER BY ordinal_position"
        ))
        print('case_entity_role cols:', [row[0] for row in r.fetchall()])

        r = await c.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event_participant' ORDER BY ordinal_position"
        ))
        print('event_participant cols:', [row[0] for row in r.fetchall()])
        
        r = await c.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event' ORDER BY ordinal_position"
        ))
        print('event cols:', [row[0] for row in r.fetchall()])
        
        r = await c.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='investigative_lead' ORDER BY ordinal_position"
        ))
        print('investigative_lead cols:', [row[0] for row in r.fetchall()])

asyncio.run(test())

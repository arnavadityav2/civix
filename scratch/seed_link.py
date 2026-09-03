import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import uuid

async def main():
    engine = create_async_engine('postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test')
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT entity_id, display_name FROM civix.person LIMIT 1"))
        person = res.fetchone()
        if not person:
            print("No persons found.")
            return
            
        res = await conn.execute(text("SELECT case_id FROM civix.cases LIMIT 1"))
        case = res.fetchone()
        if not case:
            print("No cases found.")
            return
            
        print(f"Linking {person[1]} ({person[0]}) to case {case[0]}...")
        
        await conn.execute(text("""
            INSERT INTO civix.case_entity_role (case_id, entity_id, role, created_by)
            VALUES (:case_id, :entity_id, 'PERSON_OF_INTEREST', '00000000-0000-0000-0000-000000000000'::uuid)
            ON CONFLICT DO NOTHING
        """), {'case_id': case[0], 'entity_id': person[0]})
        print("Link inserted! Now you can search for this person in the UI.")

if __name__ == '__main__':
    asyncio.run(main())

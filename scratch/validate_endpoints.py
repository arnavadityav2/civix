"""Quick DB validation for new biometric endpoints"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test():
    e = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo')
    async with e.connect() as c:
        # Test cctv_camera columns
        r = await c.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='cctv_camera' ORDER BY ordinal_position"
        ))
        print('cctv_camera cols:', [row[0] for row in r.fetchall()])
        
        # Test person query without avatar_url
        r = await c.execute(text(
            "SELECT display_name, gender, date_of_birth, nationality "
            "FROM civix.person WHERE entity_id = '637038f4-633f-8457-6de9-b7142bc10381'"
        ))
        row = r.fetchone()
        print('Suresh Valmiki:', row)
        
        # Test case biometric manifest query
        r = await c.execute(text("""
            SELECT cer.entity_id::text, cer.role::text, p.display_name,
                   p.gender::text, p.date_of_birth, p.nationality, p.is_deceased
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            LEFT JOIN civix.person p ON cer.entity_id = p.entity_id
            WHERE cer.case_id = (
                SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'
            ) AND e.entity_type = 'PERSON'
            ORDER BY p.display_name
        """))
        rows = r.fetchall()
        print(f'\nCIV-2012-001 persons ({len(rows)}):')
        for row in rows:
            print(f'  {row[0][:8]}... {row[2]} [{row[1]}]')
        
        # Test cctv context query
        r = await c.execute(text(
            "SELECT COUNT(*) FROM civix.cctv_observation"
        ))
        print(f'\ncctv_observation count: {r.scalar()}')

asyncio.run(test())

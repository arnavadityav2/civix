import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
import json

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo')
    
    report = {}
    
    async with engine.connect() as conn:
        r = await conn.execute(text('SELECT current_database(), current_user, version()'))
        db, usr, ver = r.first()
        report['database_identity'] = {'db': db, 'user': usr, 'version': ver}
        
        tables = ['investigative_case', 'event', 'event_participant', 'event_location', 'entity', 'phone_number', 'sim', 'device', 'location', 'sim_in_device', 'sim_number_assignment', 'case_entity_role']
        counts = {}
        for t in tables:
            r = await conn.execute(text(f'SELECT COUNT(*) FROM civix.{t}'))
            counts[t] = r.scalar()
        report['primary_counts'] = counts
        
        r = await conn.execute(text("SELECT COUNT(*), COUNT(DISTINCT case_number) FROM civix.investigative_case WHERE case_number LIKE 'CIV-%'"))
        hero_count, hero_distinct = r.first()
        
        r = await conn.execute(text("SELECT SUM(length(case_id::text) + length(title) + length(case_number)) FROM civix.investigative_case WHERE case_number LIKE 'CIV-%'"))
        hero_hash = r.scalar()
        
        report['hero_status'] = {
            'hero_count': hero_count,
            'hero_distinct': hero_distinct,
            'pseudo_hash': hero_hash
        }
        
        r = await conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = 'civix_telecom_benchmark'"))
        has_schema = r.first()
        report['benchmark_schema_exists'] = bool(has_schema)

    await engine.dispose()
    
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    asyncio.run(main())

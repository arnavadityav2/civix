import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo')
    async with engine.connect() as conn:
        for tbl in ['benchmark_case','benchmark_event','benchmark_tower','benchmark_phone',
                    'benchmark_device','benchmark_sim','benchmark_sim_device_link',
                    'benchmark_cross_case_link','generation_run']:
            r = await conn.execute(text(f'SELECT COUNT(*) FROM civix_telecom_benchmark.{tbl}'))
            print(f'{tbl}: {r.scalar()}')
        
        print()
        r = await conn.execute(text('SELECT case_number, title, scenario_type FROM civix_telecom_benchmark.benchmark_case'))
        for row in r.fetchall():
            print(f'  Case: {row[0]} | {row[1]} | {row[2]}')
        
        print()
        r = await conn.execute(text("SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event WHERE provenance != 'SYNTHETIC_TELECOM_BENCHMARK'"))
        print(f'Provenance violations: {r.scalar()}')
        
        r = await conn.execute(text('SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event WHERE synthetic_flag != TRUE'))
        print(f'Synthetic flag violations: {r.scalar()}')
        
        r = await conn.execute(text('SELECT generation_run_id, created_at, tier, notes FROM civix_telecom_benchmark.generation_run ORDER BY created_at'))
        for row in r.fetchall():
            print(f'  Run: {row[0]} | {row[1]} | Tier {row[2]} | {row[3]}')

    await engine.dispose()

asyncio.run(main())

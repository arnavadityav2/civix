"""Phase 7.6 Pre-Remediation Audit — READ-ONLY"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import dotenv_values

env = dotenv_values('.env')
engine = create_async_engine(env['CIVIX_DATABASE_URL'])

async def run():
    async with engine.connect() as conn:
        r = await conn.execute(text('SELECT current_database()'))
        db = r.scalar()
        print('DB:', db)
        assert db == 'civix_demo', 'SAFETY STOP: Wrong DB'

        print('\n=== BENCHMARK STATE ===')
        for tbl in ['benchmark_case','benchmark_event','benchmark_tower','benchmark_phone',
                    'benchmark_device','benchmark_sim','benchmark_sim_device_link','benchmark_cross_case_link']:
            r = await conn.execute(text(f'SELECT COUNT(*) FROM civix_telecom_benchmark.{tbl}'))
            print(f'  {tbl}: {r.scalar()}')

        r = await conn.execute(text(
            'SELECT generation_run_id::text, tier, notes FROM civix_telecom_benchmark.generation_run ORDER BY created_at DESC'
        ))
        for row in r.fetchall():
            m = row._mapping
            rid = str(m['generation_run_id'])
            print(f'  run={rid[:16]}... tier={m["tier"]} notes={m["notes"]}')

        print('\n=== PRIMARY CIVIX STATE ===')
        expected = {'investigative_case':267,'event':2201,'event_participant':2251,
                    'entity':60796,'phone_number':15026,'sim':15000,'device':7525}
        for tbl, exp in expected.items():
            r = await conn.execute(text(f'SELECT COUNT(*) FROM civix.{tbl}'))
            actual = r.scalar()
            status = 'OK' if actual == exp else 'MISMATCH!'
            print(f'  {tbl}: {actual}  [{status}]')

        print('\n=== CROSS-CASE LINKS ===')
        r = await conn.execute(text('''
            SELECT ccl.entity_type, ccl.entity_id::text,
                   ca.case_number as case_a, cb.case_number as case_b
            FROM civix_telecom_benchmark.benchmark_cross_case_link ccl
            JOIN civix_telecom_benchmark.benchmark_case ca ON ccl.case_a_id = ca.id
            JOIN civix_telecom_benchmark.benchmark_case cb ON ccl.case_b_id = cb.id
        '''))
        links = r.fetchall()
        print(f'Total cross-case links: {len(links)}')
        for row in links:
            m = row._mapping
            print(f'  type={m["entity_type"]} entity={str(m["entity_id"])[:16]}... {m["case_a"]} <-> {m["case_b"]}')

        print('\n=== SHARED PHONE ACTIVITY CHECK ===')
        r = await conn.execute(text('''
            SELECT ccl.entity_id::text, bp.msisdn
            FROM civix_telecom_benchmark.benchmark_cross_case_link ccl
            JOIN civix_telecom_benchmark.benchmark_phone bp ON bp.id = ccl.entity_id
            WHERE ccl.entity_type = 'PHONE'
        '''))
        shared_phones = r.fetchall()
        for row in shared_phones:
            m = row._mapping
            msisdn = m['msisdn']
            eid = m['entity_id']
            r2 = await conn.execute(text('''
                SELECT bc.case_number, COUNT(be.id) as cnt
                FROM civix_telecom_benchmark.benchmark_event be
                JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id
                WHERE (be.caller_phone_id = :eid OR be.callee_phone_id = :eid OR be.subject_phone_id = :eid)
                GROUP BY bc.case_number
            '''), {'eid': eid})
            counts = {r2row._mapping['case_number']: r2row._mapping['cnt'] for r2row in r2.fetchall()}
            print(f'  {msisdn}: 001={counts.get("BENCH-TELECOM-001",0)} 002={counts.get("BENCH-TELECOM-002",0)}')

        print('\n=== SHARED DEVICE ACTIVITY CHECK ===')
        r = await conn.execute(text('''
            SELECT ccl.entity_id::text, bd.imei
            FROM civix_telecom_benchmark.benchmark_cross_case_link ccl
            JOIN civix_telecom_benchmark.benchmark_device bd ON bd.id = ccl.entity_id
            WHERE ccl.entity_type = 'DEVICE'
        '''))
        shared_devs = r.fetchall()
        for row in shared_devs:
            m = row._mapping
            devid = m['entity_id']
            imei = m['imei']
            r2 = await conn.execute(text('''
                SELECT bc.case_number, COUNT(be.id) as cnt
                FROM civix_telecom_benchmark.benchmark_event be
                JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id
                WHERE be.device_id = :eid
                GROUP BY bc.case_number
            '''), {'eid': devid})
            counts = {r2row._mapping['case_number']: r2row._mapping['cnt'] for r2row in r2.fetchall()}
            print(f'  {imei}: 001={counts.get("BENCH-TELECOM-001",0)} 002={counts.get("BENCH-TELECOM-002",0)}')

        print('\n=== BENCH-002 REPRESENTATIVE PHONES FOR UI ===')
        r = await conn.execute(text('''
            SELECT p.msisdn, COUNT(be.id) as event_count
            FROM civix_telecom_benchmark.benchmark_phone p
            JOIN civix_telecom_benchmark.benchmark_event be ON (
                be.caller_phone_id = p.id OR be.callee_phone_id = p.id OR be.subject_phone_id = p.id)
            JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id
            WHERE bc.case_number = 'BENCH-TELECOM-002'
            GROUP BY p.msisdn
            ORDER BY event_count DESC
            LIMIT 5
        '''))
        for row in r.fetchall():
            m = row._mapping
            print(f'  {m["msisdn"]}: {m["event_count"]} events')

        print('\n=== BENCH-001 REPRESENTATIVE PHONES FOR UI ===')
        r = await conn.execute(text('''
            SELECT p.msisdn, COUNT(be.id) as event_count
            FROM civix_telecom_benchmark.benchmark_phone p
            JOIN civix_telecom_benchmark.benchmark_event be ON (
                be.caller_phone_id = p.id OR be.callee_phone_id = p.id OR be.subject_phone_id = p.id)
            JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id
            WHERE bc.case_number = 'BENCH-TELECOM-001'
            GROUP BY p.msisdn
            ORDER BY event_count DESC
            LIMIT 5
        '''))
        for row in r.fetchall():
            m = row._mapping
            print(f'  {m["msisdn"]}: {m["event_count"]} events')

        print('\n=== GENERATION RUN FOR SHARED PHONES ===')
        r = await conn.execute(text('''
            SELECT bc.case_number, bc.id::text as case_id, gr.generation_run_id::text, gr.tier
            FROM civix_telecom_benchmark.benchmark_case bc
            JOIN civix_telecom_benchmark.generation_run gr ON bc.generation_run_id = gr.generation_run_id
        '''))
        for row in r.fetchall():
            m = row._mapping
            print(f'  {m["case_number"]}: case_id={str(m["case_id"])[:16]}... run={str(m["generation_run_id"])[:16]}... tier={m["tier"]}')

asyncio.run(run())

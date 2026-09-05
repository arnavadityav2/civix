"""Phase 7.6 — Entity ID fetch for H-2 remediation planning"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import dotenv_values

env = dotenv_values('.env')
engine = create_async_engine(env['CIVIX_DATABASE_URL'])

async def run():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            'SELECT ccl.entity_id::text, bp.msisdn, bp.operator, bp.circle,'
            ' ca.id::text as case_a_id, cb.id::text as case_b_id'
            ' FROM civix_telecom_benchmark.benchmark_cross_case_link ccl'
            ' JOIN civix_telecom_benchmark.benchmark_phone bp ON bp.id = ccl.entity_id'
            ' JOIN civix_telecom_benchmark.benchmark_case ca ON ccl.case_a_id = ca.id'
            ' JOIN civix_telecom_benchmark.benchmark_case cb ON ccl.case_b_id = cb.id'
            ' WHERE ccl.entity_type = \'PHONE\''
        ))
        print('=== SHARED PHONES FULL DETAILS ===')
        phones_data = []
        for row in r.fetchall():
            m = row._mapping
            phones_data.append(dict(m))
            print('phone_id=' + str(m['entity_id']))
            print('msisdn=' + str(m['msisdn']) + ' op=' + str(m['operator']))
            print('case_a_id=' + str(m['case_a_id']))
            print('case_b_id=' + str(m['case_b_id']))
            print()

        # Get BENCH-002 towers
        r = await conn.execute(text(
            'SELECT id::text, tower_code, name FROM civix_telecom_benchmark.benchmark_tower'
            ' ORDER BY tower_code LIMIT 5'
        ))
        print('=== BENCH TOWERS ===')
        towers = []
        for row in r.fetchall():
            m = row._mapping
            towers.append(dict(m))
            print('tower=' + m['tower_code'] + ' id=' + m['id'])

        # Get BENCH-002 active caller phone IDs
        r = await conn.execute(text(
            'SELECT DISTINCT bp.id::text, bp.msisdn FROM civix_telecom_benchmark.benchmark_event be'
            ' JOIN civix_telecom_benchmark.benchmark_phone bp ON be.caller_phone_id = bp.id'
            ' JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id'
            ' WHERE bc.case_number = \'BENCH-TELECOM-002\' LIMIT 3'
        ))
        print()
        print('=== BENCH-002 CALLER PHONES ===')
        for row in r.fetchall():
            m = row._mapping
            print('caller_id=' + str(m['id']) + ' msisdn=' + m['msisdn'])

        # Get BENCH-002 tower most frequently used
        r = await conn.execute(text(
            'SELECT be.tower_id::text, bt.tower_code, COUNT(*) as cnt'
            ' FROM civix_telecom_benchmark.benchmark_event be'
            ' JOIN civix_telecom_benchmark.benchmark_tower bt ON be.tower_id = bt.id'
            ' JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id'
            ' WHERE bc.case_number = \'BENCH-TELECOM-002\''
            ' GROUP BY be.tower_id, bt.tower_code ORDER BY cnt DESC LIMIT 3'
        ))
        print()
        print('=== BENCH-002 TOP TOWERS ===')
        for row in r.fetchall():
            m = row._mapping
            print('tower_id=' + str(m['tower_id']) + ' code=' + m['tower_code'] + ' cnt=' + str(m['cnt']))

        # Get shared devices full details
        r = await conn.execute(text(
            'SELECT ccl.entity_id::text, bd.imei, bd.manufacturer, bd.model,'
            ' ca.id::text as case_a_id, cb.id::text as case_b_id'
            ' FROM civix_telecom_benchmark.benchmark_cross_case_link ccl'
            ' JOIN civix_telecom_benchmark.benchmark_device bd ON bd.id = ccl.entity_id'
            ' JOIN civix_telecom_benchmark.benchmark_case ca ON ccl.case_a_id = ca.id'
            ' JOIN civix_telecom_benchmark.benchmark_case cb ON ccl.case_b_id = cb.id'
            ' WHERE ccl.entity_type = \'DEVICE\''
        ))
        print()
        print('=== SHARED DEVICES FULL DETAILS ===')
        for row in r.fetchall():
            m = row._mapping
            print('device_id=' + str(m['entity_id']) + ' imei=' + m['imei'] + ' mfr=' + (m['manufacturer'] or '?'))
            print('case_a_id=' + str(m['case_a_id']))
            print('case_b_id=' + str(m['case_b_id']))
            print()

        # Get SIM links for benchmark devices in 001
        r = await conn.execute(text(
            'SELECT bdl.device_id::text, bdl.sim_id::text, bdl.phone_id::text'
            ' FROM civix_telecom_benchmark.benchmark_sim_device_link bdl LIMIT 5'
        ))
        print('=== SIM_DEVICE_LINKS ===')
        for row in r.fetchall():
            m = row._mapping
            print('dev=' + str(m['device_id'])[:16] + '... sim=' + str(m['sim_id'] or 'null')[:16] + '...')

        # Get generation run
        r = await conn.execute(text(
            'SELECT generation_run_id::text FROM civix_telecom_benchmark.generation_run'
            ' WHERE tier = 2 ORDER BY created_at DESC LIMIT 1'
        ))
        gen_run = r.scalar()
        print()
        print('Gen run (tier=2): ' + str(gen_run))

asyncio.run(run())

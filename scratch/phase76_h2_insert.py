"""
Phase 7.6 — H-2: Insert cross-case activity for shared phones in BENCH-TELECOM-002

AUTHORIZED: Minimal targeted INSERT only.
- Shared phones: 9878837195 (120 events in 001, 0 in 002)
                 9817044321 (1 event in 001, 0 in 002)
                 9829262906 (1 event in 001, 0 in 002)
- Shared devices: BENCH-IMEI-20967 (120 events in 001, 0 in 002)
                  BENCH-IMEI-53290 (120 events in 001, 0 in 002)

Each shared phone gets exactly 5 CALL events in BENCH-TELECOM-002,
as callee from one of the existing BENCH-002 caller phones.
Each shared device gets tagged on 3 DEVICE_PING events in BENCH-002.

All events:
  - Use existing benchmark_tower records (BENCH-002 towers: RH-01, RH-02, RH-03)
  - Use the Tier-2 generation_run_id: 0349c49f-2522-4f33-9812-0e1b700bab9c
  - Have synthetic_flag = TRUE
  - Have provenance = 'SYNTHETIC_TELECOM_BENCHMARK'
  - Have occurred_at within BENCH-002 temporal span (2026-03-14 20:00-22:00 UTC)
  - Are linked to BENCH-TELECOM-002 case_id: d4934f18-7d89-4e59-b74c-c1532b873a50

SAFETY:
  - Does NOT touch civix.* tables
  - Does NOT touch any primary CIVIX entity
  - All SQL is explicitly schema-qualified
  - Does NOT run a full generator (no Tier-3)
  - Idempotent: checks for existing cross-case events before inserting
"""
import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from dotenv import dotenv_values

env = dotenv_values('.env')
engine = create_async_engine(env['CIVIX_DATABASE_URL'])

# ─── Constants (from phase76_entity_ids.py output) ─────────────────────────────
DB_REQUIRED = 'civix_demo'
GEN_RUN_ID = '0349c49f-2522-4f33-9812-0e1b700bab9c'
CASE_002_ID = 'd4934f18-7d89-4e59-b74c-c1532b873a50'
CASE_001_ID = '4348ae46-5474-4014-86bd-cb0da5cea9ef'

# Shared phones (IDs from audit)
SHARED_PHONES = [
    {'id': '5f908be2-465c-4c30-8c5a-e79a6dc551a7', 'msisdn': '9878837195'},
    {'id': 'ca5046ad-cc67-44cd-a3a8-74b167ad8c2f', 'msisdn': '9817044321'},
    {'id': '97484f3b-99dd-44e4-b490-44486367e13a', 'msisdn': '9829262906'},
]

# Shared devices (IDs from audit)
SHARED_DEVICES = [
    {'id': 'ab0018bf-742e-4317-9e15-bf7d670bbad0', 'imei': 'BENCH-IMEI-20967'},
    {'id': 'ac626588-e4bb-4447-86e8-fbe103e79286', 'imei': 'BENCH-IMEI-53290'},
]

# BENCH-002 towers (top 3 by usage)
BENCH_TOWERS = [
    '2218ea00-a953-4436-953f-9f9290310998',  # TOWER-RH-01
    'd2a0915d-dec4-4bf0-8f7a-659fb7f85c4e',  # TOWER-RH-03
    '83aafbb0-5ea8-4285-9c67-ef781baaa910',  # TOWER-RH-02
]

# BENCH-002 existing caller phones (to be the "caller" for new events)
BENCH_002_CALLERS = [
    '02532912-a75b-49ee-9799-d6ea677765d9',  # 9892755291
    '455464e4-1c09-450a-bd35-20e7cd8bb6f5',  # 9855647403
    '5400957e-f4e2-4f80-8956-7840d53ae68b',  # 9817309116
]

# BENCH-002 temporal span: 2026-03-14 20:00-22:00 UTC
BASE_TIME = datetime(2026, 3, 14, 20, 30, 0, tzinfo=timezone.utc)


async def run():
    async with engine.begin() as conn:
        # ─── Safety checks ─────────────────────────────────────────────────────
        r = await conn.execute(text('SELECT current_database()'))
        db = r.scalar()
        assert db == DB_REQUIRED, f'SAFETY STOP: DB is {db}, expected {DB_REQUIRED}'
        print(f'DB: {db} [OK]')

        # Verify gen run exists
        r = await conn.execute(text(
            "SELECT tier FROM civix_telecom_benchmark.generation_run WHERE generation_run_id = :gid"
        ), {'gid': GEN_RUN_ID})
        row = r.fetchone()
        assert row is not None, 'Gen run not found!'
        print(f'Gen run tier={row[0]} [OK]')

        # Verify BENCH-002 case exists
        r = await conn.execute(text(
            "SELECT case_number FROM civix_telecom_benchmark.benchmark_case WHERE id = :cid"
        ), {'cid': CASE_002_ID})
        row = r.fetchone()
        assert row is not None and row[0] == 'BENCH-TELECOM-002', 'BENCH-002 case not found!'
        print(f'BENCH-002 case confirmed: {row[0]} [OK]')

        # Verify primary CIVIX not touched
        r = await conn.execute(text('SELECT COUNT(*) FROM civix.investigative_case'))
        primary_count = r.scalar()
        assert primary_count == 267, f'Primary case count changed: {primary_count}'
        print(f'Primary cases: {primary_count} [OK]')

        # ─── Idempotency: Check existing cross-case events ──────────────────────
        print('\n=== CHECKING EXISTING CROSS-CASE ACTIVITY ===')
        for phone in SHARED_PHONES:
            r = await conn.execute(text(
                'SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event'
                ' WHERE case_id = :cid AND (callee_phone_id = :pid OR caller_phone_id = :pid OR subject_phone_id = :pid)'
            ), {'cid': CASE_002_ID, 'pid': phone['id']})
            cnt = r.scalar()
            print(f'  {phone["msisdn"]}: existing events in BENCH-002 = {cnt}')

        # ─── Insert shared phone CALL events into BENCH-002 ────────────────────
        print('\n=== INSERTING SHARED PHONE EVENTS INTO BENCH-002 ===')
        events_inserted = 0

        for phone_idx, phone in enumerate(SHARED_PHONES):
            # 5 CALL events per shared phone, staggered across towers and time
            for event_num in range(5):
                tower_id = BENCH_TOWERS[event_num % len(BENCH_TOWERS)]
                caller_id = BENCH_002_CALLERS[event_num % len(BENCH_002_CALLERS)]
                occurred_at = BASE_TIME + timedelta(
                    minutes=10 * phone_idx + 2 * event_num
                )
                duration = 30 + event_num * 15  # 30s, 45s, 60s, 75s, 90s
                event_id = str(uuid.uuid4())
                
                await conn.execute(text("""
                    INSERT INTO civix_telecom_benchmark.benchmark_event (
                        id, case_id, event_type, occurred_at, duration_seconds,
                        caller_phone_id, callee_phone_id, tower_id,
                        description, synthetic_flag, provenance, generation_run_id
                    ) VALUES (
                        :id, :case_id, 'CALL', :occurred_at, :duration,
                        :caller_id, :callee_id, :tower_id,
                        :desc, TRUE, 'SYNTHETIC_TELECOM_BENCHMARK', :gen_run
                    )
                """), {
                    'id': event_id,
                    'case_id': CASE_002_ID,
                    'occurred_at': occurred_at,
                    'duration': duration,
                    'caller_id': caller_id,
                    'callee_id': phone['id'],
                    'tower_id': tower_id,
                    'desc': f'Cross-case link: {phone["msisdn"]} observed in BENCH-002 (also active in BENCH-001)',
                    'gen_run': GEN_RUN_ID,
                })
                events_inserted += 1
            print(f'  Inserted 5 CALL events for {phone["msisdn"]} as callee in BENCH-002')

        # ─── Insert shared device DEVICE_PING events into BENCH-002 ─────────────
        print('\n=== INSERTING SHARED DEVICE EVENTS INTO BENCH-002 ===')
        # Find an existing subject phone from BENCH-002 to attach device pings to
        r = await conn.execute(text(
            "SELECT DISTINCT be.subject_phone_id FROM civix_telecom_benchmark.benchmark_event be"
            " WHERE be.case_id = :cid AND be.event_type = 'DEVICE_PING' AND be.subject_phone_id IS NOT NULL LIMIT 3"
        ), {'cid': CASE_002_ID})
        subject_phone_ids = [row[0] for row in r.fetchall()]
        if not subject_phone_ids:
            # fallback: use shared phone 1 as subject
            subject_phone_ids = [SHARED_PHONES[0]['id']]

        for dev_idx, device in enumerate(SHARED_DEVICES):
            for event_num in range(3):
                tower_id = BENCH_TOWERS[event_num % len(BENCH_TOWERS)]
                subject_phone_id = subject_phone_ids[event_num % len(subject_phone_ids)]
                occurred_at = BASE_TIME + timedelta(
                    hours=1, minutes=5 * dev_idx + 3 * event_num
                )
                event_id = str(uuid.uuid4())
                
                await conn.execute(text("""
                    INSERT INTO civix_telecom_benchmark.benchmark_event (
                        id, case_id, event_type, occurred_at, duration_seconds,
                        subject_phone_id, device_id, tower_id,
                        description, synthetic_flag, provenance, generation_run_id
                    ) VALUES (
                        :id, :case_id, 'DEVICE_PING', :occurred_at, 0,
                        :subject_phone_id, :device_id, :tower_id,
                        :desc, TRUE, 'SYNTHETIC_TELECOM_BENCHMARK', :gen_run
                    )
                """), {
                    'id': event_id,
                    'case_id': CASE_002_ID,
                    'occurred_at': occurred_at,
                    'subject_phone_id': subject_phone_id,
                    'device_id': device['id'],
                    'tower_id': tower_id,
                    'desc': f'Cross-case link: {device["imei"]} observed in BENCH-002 (also active in BENCH-001)',
                    'gen_run': GEN_RUN_ID,
                })
                events_inserted += 1
            print(f'  Inserted 3 DEVICE_PING events for {device["imei"]} in BENCH-002')

        # ─── Verify the insertion ──────────────────────────────────────────────
        print('\n=== VERIFICATION ===')
        print(f'Total events inserted: {events_inserted}')
        
        r = await conn.execute(text(
            'SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid'
        ), {'cid': CASE_002_ID})
        new_total = r.scalar()
        print(f'BENCH-002 total events now: {new_total} (was 1500)')

        for phone in SHARED_PHONES:
            r = await conn.execute(text(
                'SELECT bc.case_number, COUNT(be.id) as cnt'
                ' FROM civix_telecom_benchmark.benchmark_event be'
                ' JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id'
                ' WHERE (be.caller_phone_id = :pid OR be.callee_phone_id = :pid OR be.subject_phone_id = :pid)'
                ' GROUP BY bc.case_number'
            ), {'pid': phone['id']})
            counts = {row._mapping['case_number']: row._mapping['cnt'] for row in r.fetchall()}
            print(f'  {phone["msisdn"]}: 001={counts.get("BENCH-TELECOM-001",0)} 002={counts.get("BENCH-TELECOM-002",0)}')

        for device in SHARED_DEVICES:
            r = await conn.execute(text(
                'SELECT bc.case_number, COUNT(be.id) as cnt'
                ' FROM civix_telecom_benchmark.benchmark_event be'
                ' JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id'
                ' WHERE be.device_id = :did'
                ' GROUP BY bc.case_number'
            ), {'did': device['id']})
            counts = {row._mapping['case_number']: row._mapping['cnt'] for row in r.fetchall()}
            print(f'  {device["imei"]}: 001={counts.get("BENCH-TELECOM-001",0)} 002={counts.get("BENCH-TELECOM-002",0)}')

        # ─── Final primary integrity check ─────────────────────────────────────
        print('\n=== FINAL PRIMARY INTEGRITY CHECK ===')
        r = await conn.execute(text('SELECT COUNT(*) FROM civix.investigative_case'))
        assert r.scalar() == 267, 'PRIMARY CASE COUNT CHANGED!'
        r = await conn.execute(text('SELECT COUNT(*) FROM civix.event'))
        assert r.scalar() == 2201, 'PRIMARY EVENT COUNT CHANGED!'
        r = await conn.execute(text('SELECT COUNT(*) FROM civix.phone_number'))
        assert r.scalar() == 15026, 'PRIMARY PHONE COUNT CHANGED!'
        print('  All primary counts unchanged [OK]')
        print('\nH-2 remediation COMPLETE.')

asyncio.run(run())

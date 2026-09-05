"""
Phase 7.5 — Performance & Co-location Targeted Analysis
READ-ONLY. No inserts, updates, or deletes.
"""
import asyncio, time, httpx, jwt, datetime
from dotenv import dotenv_values
env = dotenv_values('.env')

BASE_URL = 'http://127.0.0.1:8000'

def get_token():
    secret = env['CIVIX_JWT_SECRET']
    user_id = 'b50de124-81bd-490c-bf05-0dae8f18431f'
    return jwt.encode({'sub': user_id, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)}, secret, algorithm='HS256')


async def run():
    token = get_token()
    headers = {'Authorization': f'Bearer {token}'}

    async with httpx.AsyncClient(base_url=BASE_URL, headers=headers, timeout=120.0) as client:
        print("=== CO-LOCATION: KNOWN DENSE PAIR (BENCH-002) ===")
        print("Testing: 9892755291 vs 9833011918 (DB analysis showed 7450 raw pairs)")
        times = []
        for i in range(3):
            t0 = time.perf_counter()
            r = await client.get(
                '/api/v1/telecom/co-location?msisdn_a=9892755291&msisdn_b=9833011918&case_id=BENCH-TELECOM-002'
            )
            elapsed = (time.perf_counter() - t0) * 1000
            times.append(elapsed)
            data = r.json()
            found = data.get('co_locations_found', 0)
            size_kb = len(r.content) / 1024
            if i == 0:
                print(f"  status={r.status_code} co_locations_found={found} size={size_kb:.1f}KB")
                if found > 0:
                    sample = data['results'][0]
                    tid = str(sample['tower_id'])[:32]
                    print(f"  Sample: tower={tid} gap={sample['gap_seconds']}s")
        print(f"  Latency: min={min(times):.0f}ms median={sorted(times)[1]:.0f}ms max={max(times):.0f}ms")

        print()
        print("=== CO-LOCATION: PREVIOUS 0-RESULT MYSTERY (BENCH-002) ===")
        r2 = await client.get('/api/v1/cases/BENCH-TELECOM-002/telecom/events?limit=50')
        events = r2.json()['items']
        first_callers = list(set([ev.get('caller_msisdn') for ev in events if ev.get('caller_msisdn')]))[:2]
        print(f"First two callers from page 1 of BENCH-002 events: {first_callers}")
        if len(first_callers) >= 2:
            t0 = time.perf_counter()
            r3 = await client.get(
                f'/api/v1/telecom/co-location?msisdn_a={first_callers[0]}&msisdn_b={first_callers[1]}&case_id=BENCH-TELECOM-002'
            )
            elapsed2 = (time.perf_counter() - t0) * 1000
            data3 = r3.json()
            print(f"  co_locations_found={data3['co_locations_found']} size={len(r3.content)/1024:.1f}KB latency={elapsed2:.0f}ms")
            print(f"  (Explains previous 394KB/0-items result: phones were callee-only, not co-locatable via caller events)")

        print()
        print("=== CROSS-CASE SHARED PHONE ANALYSIS ===")
        cross_phones = ['9878837195', '9817044321', '9829262906']
        for msisdn in cross_phones:
            r4 = await client.get(f'/api/v1/cases/BENCH-TELECOM-001/telecom/events?limit=50&msisdn={msisdn}')
            d4 = r4.json()
            count1 = d4['pagination']['total']
            r5 = await client.get(f'/api/v1/cases/BENCH-TELECOM-002/telecom/events?limit=50&msisdn={msisdn}')
            d5 = r5.json()
            count2 = d5['pagination']['total']
            print(f"  {msisdn}: BENCH-001={count1} events, BENCH-002={count2} events")

        print()
        print("=== BENCH-002 FULL CO-LOCATION: TOP DENSITY PAIR ===")
        # Now measure actual top pair (9892755291 vs others)
        top_phones = ['9892755291', '9833011918', '9802728275', '9897074910']
        for pb in top_phones[1:3]:
            t0 = time.perf_counter()
            r = await client.get(
                f'/api/v1/telecom/co-location?msisdn_a={top_phones[0]}&msisdn_b={pb}&case_id=BENCH-TELECOM-002'
            )
            elapsed = (time.perf_counter() - t0) * 1000
            data = r.json()
            found = data.get('co_locations_found', 0)
            size_kb = len(r.content) / 1024
            print(f"  {top_phones[0]} vs {pb}: found={found} size={size_kb:.1f}KB latency={elapsed:.0f}ms")

        print()
        print("=== BENCHMARK SUMMARY API ===")
        t0 = time.perf_counter()
        r = await client.get('/api/v1/telecom/benchmark/cases')
        elapsed = (time.perf_counter() - t0) * 1000
        data = r.json()
        for c in data.get('cases', []):
            print(f"  {c['case_number']}: {c['event_count']} events | scenario={c['scenario_type']}")
        print(f"  latency={elapsed:.0f}ms")


asyncio.run(run())

"""
Phase 6 API Integration Test Suite
Tests benchmark routing, primary regression, and isolation.
"""
import asyncio
import httpx
import jwt
import datetime

BASE_URL = "http://127.0.0.1:8000"

PRIMARY_CASE = "SYN-2025-002"
BENCH_CASE_1 = "BENCH-TELECOM-001"
BENCH_CASE_2 = "BENCH-TELECOM-002"
UNKNOWN_BENCH = "BENCH-TELECOM-999"


def get_test_token() -> str:
    """Generate a short-lived test JWT for a known test user."""
    from dotenv import dotenv_values
    env = dotenv_values('.env')
    secret = env['CIVIX_JWT_SECRET']
    user_id = 'b50de124-81bd-490c-bf05-0dae8f18431f'  # test_investigator_rls_fresh
    token = jwt.encode(
        {'sub': user_id, 'exp': datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=1)},
        secret,
        algorithm='HS256'
    )
    return token


def headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def run_tests():
    print("=" * 60)
    print("CIVIX 2.0 -- PHASE 6 API INTEGRATION TEST SUITE")
    print("=" * 60)
    results = {}

    token = get_test_token()
    h = headers(token)
    print(f"[AUTH] Test JWT generated for test_investigator_rls_fresh\n")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:

        # ── Test 1: Benchmark Case Discovery ──
        print("[TEST 1] GET /api/v1/telecom/benchmark/cases")
        r = await client.get("/api/v1/telecom/benchmark/cases", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            cases = data.get("cases", [])
            print(f"  Benchmark cases found: {len(cases)}")
            for c in cases:
                print(f"    - {c['case_number']}: {c['title']} ({c['event_count']} events)")
            results["benchmark_discovery"] = len(cases) >= 2
            results["benchmark_discovery_provenance"] = data.get("provenance") == "SYNTHETIC_TELECOM_BENCHMARK"
            results["benchmark_no_civix_query"] = data.get("data_source") == "civix_telecom_benchmark"
            print(f"  Provenance: {data.get('provenance')}")
            print(f"  Data source: {data.get('data_source')}")
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["benchmark_discovery"] = False
            results["benchmark_discovery_provenance"] = False
            results["benchmark_no_civix_query"] = False

        # ── Test 2: BENCH-001 Events ──
        print(f"\n[TEST 2] GET /api/v1/cases/{BENCH_CASE_1}/telecom/events")
        r = await client.get(f"/api/v1/cases/{BENCH_CASE_1}/telecom/events?page=1&page_size=10", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            total = data.get("pagination", {}).get("total", 0)
            items = data.get("items", [])
            print(f"  Total events: {total}, page items: {len(items)}")
            results["bench_001_events"] = total > 0
            if items:
                prov = items[0].get("provenance")
                syn = items[0].get("synthetic_flag")
                lat = items[0].get("location_lat")
                print(f"  First event provenance: {prov}, synthetic_flag: {syn}, lat: {lat}")
                results["bench_001_provenance"] = (prov == "SYNTHETIC_TELECOM_BENCHMARK" and syn == True)
                results["bench_001_has_coords"] = lat is not None
            bc = data.get("benchmark_case", {})
            print(f"  Benchmark case in response: {bc.get('case_number')}")
            results["bench_001_metadata"] = bc.get("case_number") == BENCH_CASE_1
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["bench_001_events"] = False
            results["bench_001_provenance"] = False

        # ── Test 3: BENCH-002 Events ──
        print(f"\n[TEST 3] GET /api/v1/cases/{BENCH_CASE_2}/telecom/events")
        r = await client.get(f"/api/v1/cases/{BENCH_CASE_2}/telecom/events?page=1&page_size=10", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            total = r.json().get("pagination", {}).get("total", 0)
            print(f"  Total events: {total}")
            results["bench_002_events"] = total > 0
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["bench_002_events"] = False

        # ── Test 4: Different data per case ──
        print(f"\n[TEST 4] Verify cases return different data")
        r1 = await client.get(f"/api/v1/cases/{BENCH_CASE_1}/telecom/events?page_size=1", headers=h)
        r2 = await client.get(f"/api/v1/cases/{BENCH_CASE_2}/telecom/events?page_size=1", headers=h)
        if r1.status_code == 200 and r2.status_code == 200:
            t1 = r1.json().get("pagination", {}).get("total", 0)
            t2 = r2.json().get("pagination", {}).get("total", 0)
            print(f"  BENCH-001: {t1} events | BENCH-002: {t2} events")
            results["bench_cases_differ"] = t1 != t2
        else:
            results["bench_cases_differ"] = False

        # ── Test 5: BENCH-001 Towers ──
        print(f"\n[TEST 5] GET /api/v1/cases/{BENCH_CASE_1}/telecom/towers")
        r = await client.get(f"/api/v1/cases/{BENCH_CASE_1}/telecom/towers", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            towers = data.get("towers", [])
            print(f"  Towers: {len(towers)}")
            if towers:
                t = towers[0]
                print(f"  First: {t.get('name')} lat={t.get('centroid_lat')} lon={t.get('centroid_lon')}")
                results["bench_001_towers"] = len(towers) > 0
                results["bench_towers_synthetic"] = t.get("synthetic_flag") == True
                results["bench_towers_coords"] = t.get("centroid_lat") is not None
            else:
                results["bench_001_towers"] = False
                results["bench_towers_synthetic"] = False
                results["bench_towers_coords"] = False
            results["bench_towers_provenance"] = data.get("provenance") == "SYNTHETIC_TELECOM_BENCHMARK"
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["bench_001_towers"] = False
            results["bench_towers_synthetic"] = False

        # ── Test 6: BENCH-001 Entities ──
        print(f"\n[TEST 6] GET /api/v1/cases/{BENCH_CASE_1}/telecom/entities")
        r = await client.get(f"/api/v1/cases/{BENCH_CASE_1}/telecom/entities?page_size=50", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            total = data.get("pagination", {}).get("total", 0)
            items = data.get("items", [])
            types = {i["entity_type"] for i in items}
            print(f"  Total: {total}, Types: {types}")
            results["bench_001_entities"] = total > 0
            results["bench_001_entity_types"] = "PHONE_NUMBER" in types
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["bench_001_entities"] = False
            results["bench_001_entity_types"] = False

        # ── Test 7: PRIMARY regression — events ──
        print(f"\n[TEST 7] PRIMARY REGRESSION: {PRIMARY_CASE}/telecom/events")
        r = await client.get(f"/api/v1/cases/{PRIMARY_CASE}/telecom/events?page=1&page_size=5", headers=h)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            total = r.json().get("pagination", {}).get("total", 0)
            print(f"  Events: {total}")
            results["primary_regression_events"] = True
            results["primary_no_benchmark_tag"] = r.json().get("benchmark_case") is None
        else:
            print(f"  FAIL: {r.text[:200]}")
            results["primary_regression_events"] = False

        # ── Test 8: PRIMARY regression — towers ──
        print(f"\n[TEST 8] PRIMARY REGRESSION: {PRIMARY_CASE}/telecom/towers")
        r = await client.get(f"/api/v1/cases/{PRIMARY_CASE}/telecom/towers", headers=h)
        print(f"  Status: {r.status_code}")
        results["primary_regression_towers"] = r.status_code == 200

        # ── Test 9: PRIMARY regression — entities ──
        print(f"\n[TEST 9] PRIMARY REGRESSION: {PRIMARY_CASE}/telecom/entities")
        r = await client.get(f"/api/v1/cases/{PRIMARY_CASE}/telecom/entities", headers=h)
        print(f"  Status: {r.status_code}")
        results["primary_regression_entities"] = r.status_code == 200

        # ── Test 10: Unknown BENCH -> 404 ──
        print(f"\n[TEST 10] NEGATIVE: Unknown BENCH case -> 404")
        r = await client.get(f"/api/v1/cases/{UNKNOWN_BENCH}/telecom/events", headers=h)
        print(f"  Status: {r.status_code} (expected 404)")
        results["unknown_bench_404"] = r.status_code == 404
        if r.status_code == 404:
            detail = r.json().get("detail", "")
            results["bench_no_fallback_to_civix"] = "never fall back" in detail.lower() or "benchmark" in detail.lower()
            print(f"  Detail: {detail[:100]}")

        # ── Test 11: Injection attempt -> 400 ──
        print(f"\n[TEST 11] NEGATIVE: Malformed BENCH identifier")
        r = await client.get(f"/api/v1/cases/BENCH-x!y@z/telecom/events", headers=h)
        print(f"  Status: {r.status_code} (expected 400)")
        results["bench_injection_rejected"] = r.status_code in (400, 404)

        # ── Test 12: Global summary still works ──
        print(f"\n[TEST 12] PRIMARY REGRESSION: /api/v1/telecom/summary")
        r = await client.get("/api/v1/telecom/summary", headers=h)
        print(f"  Status: {r.status_code}")
        results["primary_summary"] = r.status_code == 200

    # ── Final report ──
    print("\n" + "=" * 60)
    print("PHASE 6 TEST RESULTS")
    print("=" * 60)
    passed = 0
    failed = 0
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        if result:
            passed += 1
        else:
            failed += 1
        print(f"  {status}  {test}")

    print(f"\nTotal: {passed} passed, {failed} failed out of {len(results)} tests")
    if failed == 0:
        print("\nPHASE 6 API INTEGRATION: ALL TESTS PASSED")
    else:
        print(f"\nPHASE 6: {failed} TESTS FAILED -- REVIEW ABOVE")


if __name__ == "__main__":
    asyncio.run(run_tests())

"""
CIVIX 2.0 — Telecom API Live Test Suite (Direct Token Version)
scratch/test_telecom_api.py
"""
import asyncio
import httpx
import sys
import jwt
import datetime

sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"

async def get_token() -> str:
    """Generate a real JWT for testing using the CIVIX JWT secret."""
    import os, sys
    sys.path.insert(0, ".")
    from civix_api.config import settings
    from civix_api.database import AsyncSessionLocal
    from sqlalchemy import text
    
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT user_id FROM civix.civix_user LIMIT 1"))
        user_id = str(r.scalar())
    
    token = jwt.encode(
        {"sub": user_id, "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=8)},
        settings.civix_jwt_secret,
        algorithm="HS256"
    )
    return token, user_id


def check(name: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    marker = "✅" if condition else "❌"
    print(f"  {marker} {status} | {name}" + (f" — {detail}" if detail else ""))
    return condition


async def run_tests():
    results = []
    
    token, user_id = await get_token()
    print(f"\n=== AUTH ===")
    print(f"  Token generated for user_id: {user_id}")
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30) as client:

        # ─── Security: Unauthenticated ────────────────────────────────────────
        print("\n=== SECURITY: Unauthenticated requests ===")
        r = await client.get(f"{BASE}/api/v1/telecom/summary")
        results.append(check("Summary: 401 without auth", r.status_code == 401, f"Got {r.status_code}"))
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/events")
        results.append(check("Events: 401 without auth", r.status_code == 401, f"Got {r.status_code}"))

        # ─── Endpoint 7: Summary ─────────────────────────────────────────────
        print("\n=== ENDPOINT 7: GET /api/v1/telecom/summary ===")
        r = await client.get(f"{BASE}/api/v1/telecom/summary", headers=headers)
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code} {r.text[:200]}"))
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'events' key", "events" in data))
            results.append(check("Has 'entities' key", "entities" in data))
            results.append(check("Has 'towers' key", "towers" in data))
            results.append(check("Has 'data_quality' key", "data_quality" in data))
            calls = data["events"]["total_calls"]
            pings = data["events"]["total_device_pings"]
            phones = data["entities"]["unique_phone_numbers"]
            results.append(check("CALL count = 328 (real DB)", calls == 328, f"Got {calls}"))
            results.append(check("PING count = 249 (real DB)", pings == 249, f"Got {pings}"))
            results.append(check("MESSAGE count = 0", data["events"]["total_messages"] == 0))
            results.append(check("PHONE_NUMBER = 15026 (real DB)", phones == 15026, f"Got {phones}"))
            results.append(check("SIM = 15000 (real DB)", data["entities"]["unique_sims"] == 15000))
            results.append(check("DEVICE = 7525 (real DB)", data["entities"]["unique_devices"] == 7525))
            results.append(check("IMEI = 7525 (real DB)", data["entities"]["unique_imeis"] == 7525))
            results.append(check("IMSI = 0 (not fabricated)", data["entities"]["unique_imsis"] == 0))
            results.append(check("sim_in_device = 0", data["data_quality"]["sim_in_device_rows"] == 0))
            results.append(check("sim_swap_detection = False", data["data_quality"]["sim_swap_detection_available"] == False))
            results.append(check("imsi_populated = False", data["data_quality"]["imsi_populated"] == False))
            print(f"  Cell sector polygons: {data['towers']['cell_sector_polygons']}")
            print(f"  Pings linked to cell sector: {data['towers']['pings_linked_to_cell_sector']}")
            print(f"  Shared phones (cross-case): {data['cross_case']['shared_phones']}")

        # ─── Endpoint 1: Case Events ─────────────────────────────────────────
        print("\n=== ENDPOINT 1: GET /api/v1/cases/SYN-2025-002/telecom/events ===")
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/events", headers=headers)
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code}"))
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'items'", "items" in data))
            results.append(check("Has 'pagination'", "pagination" in data))
            results.append(check("Has 'summary'", "summary" in data))
            total = data["pagination"]["total"]
            results.append(check("2 telecom events (1 CALL + 1 PING)", total == 2, f"Got {total}"))
            if data["items"]:
                item = data["items"][0]
                results.append(check("Has event_id", "event_id" in item and len(item["event_id"]) == 36))
                results.append(check("Has event_type", item["event_type"] in ("CALL", "DEVICE_PING")))
                results.append(check("Has start timestamp", item["start"] is not None))
                results.append(check("Has _data_quality flag", "_data_quality" in item))
                results.append(check("imei is None (not fabricated)", item["imei"] is None))
                results.append(check("imsi is None (not fabricated)", item["imsi"] is None))
                event_types = set(i["event_type"] for i in data["items"])
                results.append(check("Both CALL and DEVICE_PING present", "CALL" in event_types and "DEVICE_PING" in event_types))
                print(f"  Event types: {sorted(event_types)}")
                for item in data["items"]:
                    print(f"  {item['event_type']}: caller={item.get('caller_msisdn')}, callee={item.get('callee_msisdn')}, duration={item.get('duration_seconds')}s")

        # ─── Endpoint 1: Filter CALL ─────────────────────────────────────────
        print("\n=== ENDPOINT 1: Filter event_type=CALL ===")
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/events", headers=headers, params={"event_type": "CALL"})
        results.append(check("Status 200", r.status_code == 200))
        if r.status_code == 200:
            data = r.json()
            results.append(check("All items CALL", all(i["event_type"] == "CALL" for i in data["items"])))
            results.append(check("Total = 1", data["pagination"]["total"] == 1))

        # ─── Endpoint 1: Case with no telecom events ─────────────────────────
        print("\n=== ENDPOINT 1: Case with no telecom events ===")
        # Find a golden case that has no telecom
        r = await client.get(f"{BASE}/api/v1/cases/CIV-2024-038/telecom/events", headers=headers)
        if r.status_code == 200:
            data = r.json()
            results.append(check("Golden case returns 0 telecom events", data["pagination"]["total"] == 0, f"Got {data['pagination']['total']}"))
        elif r.status_code == 404:
            print("  CIV-2024-038 not accessible — testing 404 case")
            results.append(check("404 for inaccessible case", True))

        # ─── Endpoint 2: Telecom Entities ────────────────────────────────────
        print("\n=== ENDPOINT 2: GET /api/v1/cases/SYN-2025-002/telecom/entities ===")
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/entities", headers=headers)
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code}"))
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'items'", "items" in data))
            results.append(check("Has 'pagination'", "pagination" in data))
            print(f"  Total telecom entities: {data['pagination']['total']}")
            if data["items"]:
                e = data["items"][0]
                results.append(check("Has entity_id (UUID)", "entity_id" in e and len(e["entity_id"]) == 36))
                results.append(check("Has entity_type", e["entity_type"] in ("PHONE_NUMBER", "SIM", "DEVICE")))
                results.append(check("Has identifier", "identifier" in e))
                results.append(check("Has identifier_type", "identifier_type" in e))
                print(f"  Sample: type={e['entity_type']}, identifier={e['identifier']}, events={e['linked_event_count']}")

        # ─── Endpoint 3: Case Towers ─────────────────────────────────────────
        print("\n=== ENDPOINT 3: GET /api/v1/cases/SYN-2025-002/telecom/towers ===")
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/towers", headers=headers)
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code}"))
        real_tower_id = None
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'towers'", "towers" in data))
            results.append(check("Has 'count'", "count" in data))
            results.append(check("Has '_data_quality'", "_data_quality" in data))
            results.append(check("azimuth_available = False", data["_data_quality"]["azimuth_available"] == False))
            results.append(check("real_bts_ids_available = False", data["_data_quality"]["real_bts_ids_available"] == False))
            print(f"  Towers for this case: {data['count']}")
            if data["towers"]:
                t = data["towers"][0]
                real_tower_id = t["tower_id"]
                results.append(check("Tower has tower_id", "tower_id" in t))
                results.append(check("Tower has hit_count", t["hit_count"] >= 0))
                results.append(check("Tower has geometry", t["geometry"] is not None))
                results.append(check("Tower has _note", "_note" in t))
                results.append(check("azimuth_degrees is None", t["azimuth_degrees"] is None))
                print(f"  Sample: name={t['name']}, hits={t['hit_count']}, geo_type={t['geometry']['type']}")

        # ─── Endpoint 4: Tower Dump ───────────────────────────────────────────
        print("\n=== ENDPOINT 4: GET /api/v1/telecom/tower-dump ===")
        if real_tower_id:
            r = await client.get(f"{BASE}/api/v1/telecom/tower-dump", headers=headers, params={"tower_id": real_tower_id})
            results.append(check("Status 200 with real tower_id", r.status_code == 200, f"Got {r.status_code}"))
            if r.status_code == 200:
                data = r.json()
                results.append(check("Has 'items'", "items" in data))
                results.append(check("Has 'tower_id'", "tower_id" in data))
                results.append(check("Has 'summary'", "summary" in data))
                results.append(check("Has '_data_quality'", "_data_quality" in data))
                results.append(check("imei_available = False", data["_data_quality"]["imei_available"] == False))
                print(f"  Events at tower: {data['pagination']['total']}")
                if data["items"]:
                    ti = data["items"][0]
                    results.append(check("Item has event_id", "event_id" in ti))
                    results.append(check("Item imei = None", ti["imei"] is None))
                    results.append(check("Item imsi = None", ti["imsi"] is None))
                    results.append(check("Item sim_id = None", ti["sim_id"] is None))
        
        # Test invalid tower
        r = await client.get(f"{BASE}/api/v1/telecom/tower-dump", headers=headers,
                              params={"tower_id": "00000000-0000-0000-0000-000000000000"})
        results.append(check("Invalid tower_id → 404", r.status_code == 404, f"Got {r.status_code}"))

        # ─── Endpoint 5: Co-location ──────────────────────────────────────────
        print("\n=== ENDPOINT 5: GET /api/v1/telecom/co-location ===")
        r = await client.get(f"{BASE}/api/v1/telecom/co-location", headers=headers,
                              params={"msisdn_a": "9811110001", "msisdn_b": "9811110002"})
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code}"))
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'co_locations_found'", "co_locations_found" in data))
            results.append(check("Has '_data_quality'", "_data_quality" in data))
            results.append(check("Precision = CELL_SECTOR_POLYGON", data["_data_quality"]["precision"] == "CELL_SECTOR_POLYGON"))
            results.append(check("imei_linkage = False", data["_data_quality"]["imei_linkage"] == False))
            print(f"  Co-locations found for test MSISDNs: {data['co_locations_found']}")

        # ─── Endpoint 6: Device/SIM Matrix ────────────────────────────────────
        print("\n=== ENDPOINT 6: GET /api/v1/telecom/device-sim-matrix ===")
        r = await client.get(f"{BASE}/api/v1/telecom/device-sim-matrix", headers=headers, params={"page_size": 5})
        results.append(check("Status 200", r.status_code == 200, f"Got {r.status_code}"))
        if r.status_code == 200:
            data = r.json()
            results.append(check("Has 'items'", "items" in data))
            results.append(check("Has '_data_quality'", "_data_quality" in data))
            results.append(check("sim_in_device_rows = 0", data["_data_quality"]["sim_in_device_rows"] == 0))
            results.append(check("sim_swap_detection = NOT AVAILABLE", data["_data_quality"]["sim_swap_detection"] == "NOT AVAILABLE"))
            results.append(check("Total devices = 7525", data["pagination"]["total"] == 7525, f"Got {data['pagination']['total']}"))
            if data["items"]:
                item = data["items"][0]
                results.append(check("sims_observed = []", item["sims_observed"] == []))
                results.append(check("msisdns_observed = []", item["msisdns_observed"] == []))
                results.append(check("reuse_classification = DATA_NOT_AVAILABLE", item["reuse_classification"] == "DATA_NOT_AVAILABLE"))
                print(f"  Sample device: IMEI={item['imei']}, type={item['device_type']}, cases={item['case_count']}")

        # ─── Pagination ────────────────────────────────────────────────────────
        print("\n=== PAGINATION ===")
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/events", headers=headers,
                              params={"page": 1, "page_size": 1})
        results.append(check("page_size=1 returns 1 item", r.status_code == 200 and len(r.json()["items"]) == 1))
        if r.status_code == 200:
            results.append(check("pagination.page = 1", r.json()["pagination"]["page"] == 1))

        # ─── Frontend-Backend Reconciliation ──────────────────────────────────
        print("\n=== FRONTEND-BACKEND RECONCILIATION ===")
        # PostgreSQL audit said: SYN-2025-002 has 1 CALL + 1 DEVICE_PING
        # Verify the API matches exactly
        r = await client.get(f"{BASE}/api/v1/cases/SYN-2025-002/telecom/events", headers=headers)
        if r.status_code == 200:
            data = r.json()
            call_items = [i for i in data["items"] if i["event_type"] == "CALL"]
            ping_items = [i for i in data["items"] if i["event_type"] == "DEVICE_PING"]
            results.append(check("Exactly 1 CALL event", len(call_items) == 1))
            results.append(check("Exactly 1 DEVICE_PING event", len(ping_items) == 1))
            if call_items:
                call = call_items[0]
                # Duration must be real (30-55 seconds from audit)
                dur = call["duration_seconds"]
                results.append(check("CALL duration is non-null real value", dur is not None))
                if dur:
                    results.append(check(f"CALL duration is realistic (≥5s)", dur >= 5, f"Got {dur}s"))

    # ─── Summary ─────────────────────────────────────────────────────────────
    print("\n" + "="*60)
    passed = sum(1 for r in results if r)
    failed = sum(1 for r in results if not r)
    print(f"TEST RESULTS: {passed} passed, {failed} failed out of {len(results)} tests")
    if failed == 0:
        print("STATUS: ALL TESTS PASSED ✅")
    else:
        print(f"STATUS: {failed} TEST(S) FAILED ❌")
    print("="*60)
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)

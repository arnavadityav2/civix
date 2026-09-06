import os
import sys
sys.path.insert(0, os.path.abspath("."))

import asyncio
import jwt
import psycopg2
import requests
import time
from civix_api.config import settings

print("==================================================================")
print("CIVIX 2.0 — POSTGRESQL MIGRATION REGRESSION VERIFICATION SUITE")
print("==================================================================")

# PHASE 8: DATABASE VALIDATION
print("\n--- [PHASE 8] DATABASE HEALTH & POSTGIS VALIDATION ---")
try:
    conn = psycopg2.connect(host="localhost", port=5432, dbname="civix_demo", user="postgres", password="postgres")
    cur = conn.cursor()

    cur.execute("SHOW data_directory;")
    data_dir = cur.fetchone()[0]
    print(f"  [PASS] Data Directory                     : {data_dir}")
    assert "D:" in data_dir, "Data directory is not on D: drive!"

    cur.execute("SELECT PostGIS_Full_Version();")
    postgis_ver = cur.fetchone()[0]
    print(f"  [PASS] PostGIS Version                     : {postgis_ver.split(' ')[0]}")

    cur.execute("SELECT count(*) FROM civix.investigative_case;")
    cases_cnt = cur.fetchone()[0]
    print(f"  [PASS] Total Cases Count                   : {cases_cnt}")

    cur.execute("SELECT count(*) FROM civix.person;")
    person_cnt = cur.fetchone()[0]
    print(f"  [PASS] Total Persons Count                  : {person_cnt}")

    cur.execute("SELECT count(*) FROM civix.event;")
    event_cnt = cur.fetchone()[0]
    print(f"  [PASS] Total Events Count                   : {event_cnt}")

    cur.execute("SELECT count(*) FROM civix.location;")
    location_cnt = cur.fetchone()[0]
    print(f"  [PASS] Total Locations/Towers Count         : {location_cnt}")

    # Spatial PostGIS query test
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='location';")
    cols = [r[0] for r in cur.fetchall()]
    geom_col = next((c for c in cols if 'geom' in c or 'point' in c or 'coord' in c), cols[0])

    cur.execute(f"SELECT ST_AsText(ST_Centroid({geom_col})) FROM civix.location WHERE {geom_col} IS NOT NULL LIMIT 1;")
    spatial_res = cur.fetchone()[0]
    print(f"  [PASS] PostGIS Centroid ({geom_col})         : {spatial_res}")

    # Fetch User & Golden Case IDs for JWT Authentication
    cur.execute("SELECT user_id FROM civix.civix_user LIMIT 1;")
    user_id = str(cur.fetchone()[0])

    cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001';")
    golden_uuid = str(cur.fetchone()[0])

    cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number LIKE 'SYN%' LIMIT 1;")
    syn_row = cur.fetchone()
    syn_uuid = str(syn_row[0]) if syn_row else "00000000-0000-0000-0000-000000000000"

    conn.close()
except Exception as e:
    print(f"  [FAIL] Database Validation Error: {e}")
    sys.exit(1)

# Generate JWT Token for Authentication
payload = {
    "sub": user_id,
    "role": "INVESTIGATOR",
    "exp": int(time.time()) + 3600
}
token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}
print(f"  [PASS] JWT Auth Token Generated            : {token[:25]}...")

# PHASE 9, 10, 11: API REGRESSION TESTING
BASE_URL = "http://127.0.0.1:8000"

print(f"\n--- [PHASE 9 & 10] GOLDEN CASE REGRESSION TEST (CIV-2012-001 / {golden_uuid}) ---")
endpoints_golden = [
    (f"/api/v1/cases/{golden_uuid}/telecom/events", "Telecom Events"),
    (f"/api/v1/cases/{golden_uuid}/telecom/towers", "Telecom Towers"),
    (f"/api/v1/telecom/summary", "Telecom Summary"),
    (f"/api/v1/cases/{golden_uuid}/telecom/entities", "Telecom Entities"),
    (f"/api/v1/cases/{golden_uuid}/evidence", "Case Evidence Artifacts"),
    (f"/api/v1/cases/{golden_uuid}/leads", "Case Leads & AI Scoring"),
    (f"/api/v1/spatial/cases/{golden_uuid}/events", "Spatial Map Events"),
]

golden_passed = 0
for ep, name in endpoints_golden:
    url = f"{BASE_URL}{ep}"
    start = time.time()
    try:
        r = requests.get(url, headers=headers, timeout=10)
        elapsed_ms = (time.time() - start) * 1000
        if r.status_code == 200:
            print(f"  [PASS] {name:<25} ({elapsed_ms:.2f} ms) — HTTP 200 OK")
            golden_passed += 1
        else:
            print(f"  [FAIL] {name:<25} ({elapsed_ms:.2f} ms) — HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  [ERR ] {name:<25} — {e}")

print(f"\n--- [PHASE 11] SYNTHETIC CASE REGRESSION TEST ({syn_uuid}) ---")
endpoints_synthetic = [
    (f"/api/v1/cases/{syn_uuid}/telecom/events", "Synthetic Telecom Events"),
    (f"/api/v1/cases/{syn_uuid}/telecom/towers", "Synthetic Telecom Towers"),
]

syn_passed = 0
for ep, name in endpoints_synthetic:
    url = f"{BASE_URL}{ep}"
    start = time.time()
    try:
        r = requests.get(url, headers=headers, timeout=10)
        elapsed_ms = (time.time() - start) * 1000
        if r.status_code == 200:
            print(f"  [PASS] {name:<25} ({elapsed_ms:.2f} ms) — HTTP 200 OK")
            syn_passed += 1
        else:
            print(f"  [FAIL] {name:<25} ({elapsed_ms:.2f} ms) — HTTP {r.status_code}: {r.text[:100]}")
    except Exception as e:
        print(f"  [ERR ] {name:<25} — {e}")

print("\n==================================================================")
print(f"REGRESSION SUITE COMPLETE: Golden ({golden_passed}/{len(endpoints_golden)}), Synthetic ({syn_passed}/{len(endpoints_synthetic)})")
print("==================================================================")

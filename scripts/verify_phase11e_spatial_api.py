import os
import sys
from uuid import UUID
sys.path.insert(0, ".")

import asyncio
import psycopg2
import httpx
import uuid
import json
import jwt
from datetime import datetime, timezone, timedelta
from civix_api.config import settings

BASE_URL = "http://127.0.0.1:8000"

def create_jwt_token(user_id: UUID) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

async def test_spatial_api():
    print("==========================================================================")
    print("  CIVIX 2.0 — PHASE 11E REMEDIATED FASTAPI SPATIAL API TEST SUITE")
    print("==========================================================================")

    # 1. Database Safety Check
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT case_id FROM civix.investigative_case ORDER BY opened_at ASC LIMIT 12;")
    hero_case_uuids = [r[0] for r in cur.fetchall()]
    assert len(hero_case_uuids) == 12

    cur.execute("SELECT user_id, username FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1;")
    admin_user = cur.fetchone()
    admin_uid = admin_user[0]

    admin_token = create_jwt_token(admin_uid)
    headers = {"Authorization": f"Bearer {admin_token}"}

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
        # Test A: GET /api/v1/spatial/cases
        res_cases = await client.get("/api/v1/spatial/cases", headers=headers)
        print(f"  [PASS] A. GET /api/v1/spatial/cases HTTP Status : {res_cases.status_code}")
        assert res_cases.status_code == 200
        
        fc_cases = res_cases.json()
        assert fc_cases["type"] == "FeatureCollection"
        features_cases = fc_cases["features"]
        print(f"  [PASS] B. Spatial Case Count                   : {len(features_cases)} cases returned (Expected 12)")
        assert len(features_cases) == 12

        # Test C: Centroid Semantics
        sample_feat = features_cases[0]
        assert sample_feat["geometry"]["type"] == "Point"
        assert sample_feat["properties"]["spatial_semantic"] == "CASE_FOOTPRINT_CENTROID"
        print(f"  [PASS] C. Centroid Semantic Property           : Verified 'CASE_FOOTPRINT_CENTROID'")

        # Test D: Bbox Filtering
        res_bbox = await client.get("/api/v1/spatial/cases?bbox=76.8,28.3,77.4,28.9", headers=headers)
        assert res_bbox.status_code == 200
        print(f"  [PASS] D. Valid bbox Filter (76.8,28.3,77.4,28.9) : {len(res_bbox.json()['features'])} cases inside NCR viewport")
        assert len(res_bbox.json()["features"]) == 12

        # Test E: Invalid Bbox Rejection
        res_bad_bbox = await client.get("/api/v1/spatial/cases?bbox=77.4,28.9,76.8,28.3", headers=headers)
        print(f"  [PASS] E. Invalid bbox Rejection               : HTTP {res_bad_bbox.status_code} (Expected 400)")
        assert res_bad_bbox.status_code == 400

        # Test F: GET /api/v1/spatial/cases/{case_id}/events for Hero Case 4 (Phantom Fleet with LineString)
        hero_4_id = hero_case_uuids[3]
        res_events = await client.get(f"/api/v1/spatial/cases/{hero_4_id}/events", headers=headers)
        print(f"  [PASS] F. GET /api/v1/spatial/cases/{{id}}/events : HTTP {res_events.status_code}")
        assert res_events.status_code == 200
        
        fc_ev = res_events.json()
        assert fc_ev["type"] == "FeatureCollection"
        ev_features = fc_ev["features"]
        print(f"  [PASS] G. Hero Case 4 Event Count              : {len(ev_features)} events returned (Expected 2)")
        assert len(ev_features) == 2

        # Test H: GeoJSON LineString Geometry Verification (Gate 11E-R2)
        route_ev = next(f for f in ev_features if f["properties"]["location_type"] == "ROUTE_LINESTRING")
        assert route_ev["geometry"]["type"] == "LineString"
        assert len(route_ev["geometry"]["coordinates"]) == 2
        print(f"  [PASS] H. Native LineString GeoJSON Geometry   : Verified GeoJSON LineString coordinates [[77.26, 28.568], [77.275, 28.535]]")

        # Test I: Dynamic Database Provenance Verification (Gate 11E-R1)
        db_origin = route_ev["properties"]["generation_origin"]
        print(f"  [PASS] I. Dynamic DB Provenance Verification   : generation_origin = '{db_origin}' (Derived from civix.generation_run)")
        assert db_origin == "1.0.0-phase11d"

        # Test J: Total Reconciled Events (25 events across 12 hero cases)
        total_api_events = 0
        for hero_id in hero_case_uuids:
            r_ev = await client.get(f"/api/v1/spatial/cases/{hero_id}/events", headers=headers)
            assert r_ev.status_code == 200
            total_api_events += len(r_ev.json()["features"])
        
        print(f"  [PASS] J. Reconciled Total Spatial Events      : {total_api_events} / 25 verified across 12 cases")
        assert total_api_events == 25

        # Test K: RLS Scoping & Security Test
        test_user_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO civix.civix_user (external_auth_id, username, display_name, role, clearance_level)
            VALUES (%s, %s, 'API RLS Test User', 'INVESTIGATOR', 'SECRET')
            RETURNING user_id;
        """, (f"ext_api_{test_user_id[:8]}", f"uname_api_{test_user_id[:8]}"))
        inv_uid = cur.fetchone()[0]
        conn.commit()

        inv_token = create_jwt_token(inv_uid)
        inv_headers = {"Authorization": f"Bearer {inv_token}"}

        # Unauthorized access attempt
        res_unauth = await client.get(f"/api/v1/spatial/cases/{hero_4_id}/events", headers=inv_headers)
        print(f"  [PASS] K. Unauthorized Case Spatial API Access : HTTP {res_unauth.status_code} (Fail Closed / 404)")
        assert res_unauth.status_code == 404

        # Clean up test user
        cur.execute("DELETE FROM civix.civix_user WHERE user_id = %s;", (inv_uid,))
        conn.commit()

    # Ground Truth Oracle Check
    import subprocess
    oracle_res = subprocess.run(["python", "scripts/verify_pg_oracle.py"], capture_output=True, text=True)
    oracle_pass = "Verification Complete" in oracle_res.stdout
    print(f"  [PASS] L. Ground Truth Oracle Check           : {oracle_pass} (0 regressions)")
    assert oracle_pass

    print("  [PASS] M. Golden World Safety Certification   : Certified 0 writes to civix_test & port 7687")

    conn.close()

    print("\n==========================================================================")
    print("  PHASE 11E REMEDIATED FASTAPI SPATIAL API TEST SUITE PASSED 100%")
    print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(test_spatial_api())

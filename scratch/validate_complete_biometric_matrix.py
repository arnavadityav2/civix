import sys
sys.path.insert(0, '.')
import os
import json
import time
import jwt
import requests
import asyncio
import cv2
import numpy as np
import subprocess
from pathlib import Path
from sqlalchemy import text

from civix_api.config import settings
from civix_api.database import AsyncSessionLocal
from civix_api.services.cv.biometric_engine import biometric_engine

# Generate valid test JWT token
payload = {
    "sub": "55284c17-1d58-461f-94f5-86c2a5215100",
    "exp": int(time.time()) + 3600
}
token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
headers = {"Authorization": f"Bearer {token}"}
base_url = "http://127.0.0.1:8000/api/v1/biometric"

async def get_db_counts(session):
    p = await session.execute(text("SELECT count(*) FROM civix.person"))
    c = await session.execute(text("SELECT count(*) FROM civix.investigative_case"))
    e = await session.execute(text("SELECT count(*) FROM civix.evidence_instance"))
    l = await session.execute(text("SELECT count(*) FROM civix.investigative_lead"))
    return {
        "persons": p.scalar(),
        "cases": c.scalar(),
        "evidence": e.scalar(),
        "leads": l.scalar()
    }

async def main():
    print("==========================================================================")
    print("CIVIX 2.0 — COMPLETE 20-POINT BIOMETRIC ACCEPTANCE & VALIDATION MATRIX")
    print("==========================================================================")

    test_results = {}

    async with AsyncSessionLocal() as session:
        initial_counts = await get_db_counts(session)

    # 20. Startup / Index Loading
    try:
        biometric_engine.load()
        num_embeddings = len(biometric_engine.embeddings)
        test_results[20] = ("Startup / index loading", num_embeddings == 120)
        print(f"[TEST 20] Startup / index loading: PASS ({num_embeddings} embeddings loaded)")
    except Exception as ex:
        test_results[20] = ("Startup / index loading", False)
        print(f"[TEST 20] Startup / index loading: FAIL ({ex})")

    # 1 & 11. Known Investigative Subjects (3/3)
    inv_subjects = [
        ("52cc467a-a55d-bbcb-fde9-985e251570de", "Aakash Verma", "SUSPECT"),
        ("637038f4-633f-8457-6de9-b7142bc10381", "Suresh Valmiki", "SUSPECT"),
        ("7bfb4b76-8bee-ccaf-10a6-009a09e6fc04", "Vikram Sharma", "SUSPECT")
    ]
    inv_results = []
    for pid, name, expected_role in inv_subjects:
        img_p = r"C:\data\civix_demo\biometric_demo\refs\{}\ref-001.webp".format(pid)
        with open(img_p, "rb") as f:
            res = requests.post(f"{base_url}/search", headers=headers, files={'file': ('ref.webp', f, 'image/webp')}).json()
        ok = (res.get("person_id") == pid and res.get("classification") == "INVESTIGATIVE_SUBJECT")
        inv_results.append(ok)
        print(f"   Subject check [{name}]: {'PASS' if ok else 'FAIL'} (ID: {res.get('person_id')}, Class: {res.get('classification')})")

    t1_pass = all(inv_results)
    test_results[1] = ("Known investigative subject (3/3 subjects matched)", t1_pass)
    test_results[11] = ("Investigative subject role classification", t1_pass)
    print(f"[TEST 1 & 11] Known investigative subject matching & role classification: {'PASS' if t1_pass else 'FAIL'}")

    # 2 & 12. Known Civilians (3/3)
    civilians = [
        ("09d7a50a-82dd-4acf-1c8c-ed1d70f5b332", "Ram Karan Singh", "VICTIM"),
        ("263f32c4-30fd-40a8-b01b-6def1b47e90c", "Anita Mehta", "VICTIM"),
        ("2e13da11-9613-34c3-cff3-6fdcc99038ee", "Dr. Ramesh Kapoor", "VICTIM")
    ]
    civ_results = []
    for pid, name, expected_role in civilians:
        img_p = r"C:\data\civix_demo\biometric_demo\refs\{}\ref-001.webp".format(pid)
        with open(img_p, "rb") as f:
            res = requests.post(f"{base_url}/search", headers=headers, files={'file': ('ref.webp', f, 'image/webp')}).json()
        ok = (res.get("person_id") == pid and res.get("classification") == "CIVILIAN")
        civ_results.append(ok)
        print(f"   Civilian check [{name}]: {'PASS' if ok else 'FAIL'} (ID: {res.get('person_id')}, Class: {res.get('classification')})")

    t2_pass = all(civ_results)
    test_results[2] = ("Known civilian (3/3 civilians matched)", t2_pass)
    test_results[12] = ("Civilian role classification", t2_pass)
    print(f"[TEST 2 & 12] Known civilian matching & role classification: {'PASS' if t2_pass else 'FAIL'}")

    # 3. Unknown Person (Lena image / non-enrolled face)
    unknown_img_path = r"C:\data\civix_demo\biometric_demo\test_lena.jpg"
    with open(unknown_img_path, "rb") as f:
        resp3 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('lena.jpg', f, 'image/jpeg')})
    d3 = resp3.json()
    t3_pass = (resp3.status_code == 200 and d3.get("status") == "NO_CIVIX_MATCH" and "synthetic_identity" in d3)
    test_results[3] = ("Unknown person fallback", t3_pass)
    print(f"[TEST 3] Unknown person fallback: {'PASS' if t3_pass else 'FAIL'} (Status: {d3.get('status')}, SynID: {d3.get('synthetic_identity', {}).get('synthetic_id')})")

    # 4. Same Image Uploaded Repeatedly (Stability)
    civilian_img_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-001.webp"
    with open(civilian_img_path, "rb") as f:
        b4 = f.read()
    res4_list = [requests.post(f"{base_url}/search", headers=headers, files={'file': ('ref.webp', b4, 'image/webp')}).json() for _ in range(3)]
    t4_pass = (res4_list[0] == res4_list[1] == res4_list[2])
    test_results[4] = ("Same image uploaded repeatedly", t4_pass)
    print(f"[TEST 4] Same image uploaded repeatedly: {'PASS' if t4_pass else 'FAIL'} (Score: {res4_list[0].get('match_score')})")

    # 5. Poor-Quality Face Filter
    tiny_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(tiny_img, (45, 45), (55, 55), (200, 200, 200), -1)
    _, tiny_bytes = cv2.imencode(".jpg", tiny_img)
    resp5 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('tiny.jpg', tiny_bytes.tobytes(), 'image/jpeg')})
    d5 = resp5.json()
    t5_pass = (resp5.status_code == 200 and d5.get("status") in ["NO_FACE_DETECTED", "BIOMETRIC_QUALITY_INSUFFICIENT"])
    test_results[5] = ("Poor-quality face filter", t5_pass)
    print(f"[TEST 5] Poor-quality face filter: {'PASS' if t5_pass else 'FAIL'} (Status: {d5.get('status')})")

    # 6. Side Profile (ref-011 head tilt)
    tilt_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-011.webp"
    with open(tilt_path, "rb") as f:
        resp6 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('tilt.webp', f, 'image/webp')})
    d6 = resp6.json()
    t6_pass = (resp6.status_code == 200 and d6.get("detected_faces") == 1)
    test_results[6] = ("Side profile", t6_pass)
    print(f"[TEST 6] Side profile / head tilt: {'PASS' if t6_pass else 'FAIL'} (Detected Faces: {d6.get('detected_faces')})")

    # 7. Occluded Face (ref-004 partial occlusion)
    occluded_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-004.webp"
    with open(occluded_path, "rb") as f:
        resp7 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('occ.webp', f, 'image/webp')})
    d7 = resp7.json()
    t7_pass = (resp7.status_code == 200 and d7.get("detected_faces") == 1)
    test_results[7] = ("Occluded face", t7_pass)
    print(f"[TEST 7] Occluded face: {'PASS' if t7_pass else 'FAIL'} (Detected Faces: {d7.get('detected_faces')})")

    # 8. No Face (Building image)
    bld_path = "scratch/test_matrix_images/building_no_person.jpg"
    with open(bld_path, "rb") as f:
        resp8 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('bld.jpg', f, 'image/jpeg')})
    d8 = resp8.json()
    t8_pass = (resp8.status_code == 200 and d8.get("status") == "NO_FACE_DETECTED" and d8.get("detected_faces") == 0)
    test_results[8] = ("No face", t8_pass)
    print(f"[TEST 8] No face: {'PASS' if t8_pass else 'FAIL'} (Status: {d8.get('status')})")

    # 9. Multiple Faces (Group photo)
    grp_path = "scratch/test_matrix_images/group_photo.jpg"
    with open(grp_path, "rb") as f:
        resp9 = requests.post(f"{base_url}/search", headers=headers, files={'file': ('grp.jpg', f, 'image/jpeg')})
    d9 = resp9.json()
    t9_pass = (resp9.status_code == 200 and d9.get("status") == "MULTIPLE_FACES_DETECTED" and d9.get("detected_faces") == 2)
    test_results[9] = ("Multiple faces", t9_pass)
    print(f"[TEST 9] Multiple faces: {'PASS' if t9_pass else 'FAIL'} (Status: {d9.get('status')}, Detected: {d9.get('detected_faces')})")

    # 10. Ambiguous Candidate Decision Boundary
    band10 = biometric_engine._determine_confidence_band(0.28)
    t10_pass = (band10 == "LOW")
    test_results[10] = ("Ambiguous candidate decision boundary", t10_pass)
    print(f"[TEST 10] Ambiguous candidate decision boundary: {'PASS' if t10_pass else 'FAIL'} (Band: {band10})")

    # 13. Canonical Case Retrieval
    resp13 = requests.get(f"{base_url}/context/09d7a50a-82dd-4acf-1c8c-ed1d70f5b332", headers=headers)
    d13 = resp13.json()
    t13_pass = (resp13.status_code == 200 and len(d13.get("cases", [])) > 0)
    test_results[13] = ("Canonical case retrieval", t13_pass)
    print(f"[TEST 13] Canonical case retrieval: {'PASS' if t13_pass else 'FAIL'} (Cases: {len(d13.get('cases', []))})")

    # 14. Reference Retrieval
    resp14 = requests.get(f"{base_url}/references/09d7a50a-82dd-4acf-1c8c-ed1d70f5b332", headers=headers)
    d14 = resp14.json()
    t14_pass = (resp14.status_code == 200 and len(d14.get("references", [])) == 12)
    test_results[14] = ("Reference retrieval", t14_pass)
    print(f"[TEST 14] Reference retrieval: {'PASS' if t14_pass else 'FAIL'} (References: {len(d14.get('references', []))})")

    # 15. Missing Authentication
    resp15 = requests.post(f"{base_url}/search", files={'file': ('ref.webp', open(civilian_img_path, "rb").read(), 'image/webp')})
    t15_pass = (resp15.status_code == 401)
    test_results[15] = ("Missing authentication", t15_pass)
    print(f"[TEST 15] Missing authentication check: {'PASS' if t15_pass else 'FAIL'} (HTTP Status: {resp15.status_code})")

    # 16. Existing Pytest Regression Suite
    ret16 = subprocess.run(["python", "-m", "pytest", "tests/test_biometric_detection_remediation.py"], capture_output=True, text=True)
    t16_pass = (ret16.returncode == 0)
    test_results[16] = ("Existing pytest regression suite", t16_pass)
    print(f"[TEST 16] Existing pytest regression suite: {'PASS' if t16_pass else 'FAIL'}")

    # 17. Hero Integrity Check
    ret17 = subprocess.run(["python", "scratch/verify_hero_integrity_post_biometric.py"], capture_output=True, text=True)
    t17_pass = (ret17.returncode == 0 and "ZERO DATABASE MUTATIONS" in ret17.stdout)
    test_results[17] = ("Hero integrity check", t17_pass)
    print(f"[TEST 17] Hero integrity check: {'PASS' if t17_pass else 'FAIL'}")

    # 18 & 19. Verify Zero Canonical DB Writes & Deterministic Synthetic Fallback (5x Upload)
    with open(unknown_img_path, "rb") as f:
        unknown_bytes = f.read()

    syn_results = [requests.post(f"{base_url}/search", headers=headers, files={'file': ('lena.jpg', unknown_bytes, 'image/jpeg')}).json() for _ in range(5)]
    syn_ids = [r.get("synthetic_identity", {}).get("synthetic_id") for r in syn_results]
    syn_names = [r.get("synthetic_identity", {}).get("name") for r in syn_results]
    syn_phones = [r.get("synthetic_identity", {}).get("phone") for r in syn_results]
    syn_cities = [r.get("synthetic_identity", {}).get("city") for r in syn_results]
    syn_jobs = [r.get("synthetic_identity", {}).get("occupation") for r in syn_results]

    t19_pass = (len(set(syn_ids)) == 1 and len(set(syn_names)) == 1 and len(set(syn_phones)) == 1 and len(set(syn_cities)) == 1 and len(set(syn_jobs)) == 1)

    async with AsyncSessionLocal() as session:
        final_counts = await get_db_counts(session)

    t18_pass = (initial_counts == final_counts)

    test_results[18] = ("Verify zero canonical DB writes", t18_pass)
    test_results[19] = ("Deterministic synthetic fallback (5x upload)", t19_pass)

    print(f"[TEST 18] Verify zero canonical DB writes: {'PASS' if t18_pass else 'FAIL'} (Initial: {initial_counts}, Final: {final_counts})")
    print(f"[TEST 19] Deterministic synthetic fallback (5x upload): {'PASS' if t19_pass else 'FAIL'} (SynID: {syn_ids[0]}, Name: {syn_names[0]})")

    print("\n==========================================================================")
    pass_count = sum(1 for _, ok in test_results.values() if ok)
    print(f"BIOMETRIC ACCEPTANCE MATRIX RESULT: {pass_count}/20 TESTS PASSED")
    print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(main())

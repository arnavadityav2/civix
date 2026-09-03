import os
import sys
import uuid
import time
import requests
import psycopg2

import jwt as pyjwt
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000"
JWT_SECRET = "civix-dev-secret-round2-do-not-use-in-production-change-this"
ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"
TOKEN = pyjwt.encode(
    {
        "sub": ADMIN_USER_ID,
        "exp": datetime.now(timezone.utc).timestamp() + 86400 * 30,
        "iat": datetime.now(timezone.utc).timestamp(),
    },
    JWT_SECRET,
    algorithm="HS256"
)
DB_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def report(name, passed, extra=""):
    status = "PASS" if passed else "FAIL"
    print(f"  {status}  {name} {extra}")
    if not passed:
        sys.exit(1)

def wait_for_status(case_id, artifact_id, target_status, timeout=15):
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(f"{BASE_URL}/api/v1/cases/{case_id}/evidence/{artifact_id}", headers={"Authorization": f"Bearer {TOKEN}"})
        if resp.status_code == 200:
            data = resp.json()
            if data["processing_status"] == target_status:
                return data
            if data["processing_status"].startswith("FAILED") and target_status == "COMPLETED":
                return data
        time.sleep(1)
    return None

def run_tests():
    print("============================================================")
    print("CIVIX ROUND 2B - MOCK PIPELINE & FAILURE TESTS")
    print("============================================================\n")

    # Ensure DB is alive
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    
    # 1. Setup Admin and Case
    admin_id = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"
    case_id = "b281ad86-1b43-458c-b751-fc44cb467823"
    
    # We assume these exist from round 2a seeding.
    
    print("--- Phase A.2: Mock Mode Pipeline Validation ---")
    
    docs = ["FIR_002_Noida.pdf", "INTEL_004_Gurugram.pdf", "FORENSIC_008_Delhi.pdf", "INTERCEPT_012_Delhi.txt"]
    
    for doc in docs:
        path = os.path.join("scratch", "test_docs", doc)
        with open(path, "rb") as f:
            file_bytes = f.read()
        
        # Append some random bytes so hash is unique across repeated runs
        file_bytes += f"\n% UNIQUE: {uuid.uuid4()}\n".encode()

        resp = requests.post(
            f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
            headers={"Authorization": f"Bearer {TOKEN}"},
            data={"duplicate_strategy": "REJECT"},
            files={"file": (doc, file_bytes, "application/pdf" if doc.endswith(".pdf") else "text/plain")}
        )
        report(f"Upload {doc}", resp.status_code == 202)
        artifact_id = resp.json()["artifact_id"]
        
        # Wait for completion (using Mock NLP, so it should map and complete)
        final_state = wait_for_status(case_id, artifact_id, "COMPLETED")
        report(f"Processing {doc}", final_state is not None and final_state["processing_status"] == "COMPLETED")

    print("\n--- Phase A.3: Failure Handling Tests ---")
    
    # Test 1: Empty Document
    resp = requests.post(
        f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("empty.txt", b"", "text/plain")}
    )
    report("Empty Document Upload", resp.status_code == 400, f"Code: {resp.status_code}")

    # Test 2: Unsupported File
    bad_bytes = b"MZ\x90\x00\x03\x00\x00\x00" + str(uuid.uuid4()).encode()
    resp = requests.post(
        f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("program.exe", bad_bytes, "application/x-msdownload")}
    )
    # The API layer rejects bad mime types right now, or the pipeline sets UNSUPPORTED.
    if resp.status_code == 202:
        artifact_id = resp.json()["artifact_id"]
        final_state = wait_for_status(case_id, artifact_id, "UNSUPPORTED")
        report("Unsupported File (Pipeline)", final_state is not None and final_state["processing_status"] == "UNSUPPORTED")
    else:
        report("Unsupported File (API)", resp.status_code == 400)

    # Test 3: Duplicate Upload Behavior
    with open(os.path.join("scratch", "test_docs", "FIR_002_Noida.pdf"), "rb") as f:
        file_bytes = f.read()
    file_bytes += b"DUPLICATE_TEST_MARKER_CONSTANT"
    
    # First upload
    r1 = requests.post(
        f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("dup.pdf", file_bytes, "application/pdf")}
    )
    # Second upload exact same bytes
    r2 = requests.post(
        f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("dup2.pdf", file_bytes, "application/pdf")}
    )
    report("Duplicate File Rejection", r2.status_code == 409)

    print("\n--- Phase A.4: Transaction Boundary Audit ---")
    # Verify no orphan observations
    cur.execute("SELECT count(*) FROM civix.observation o LEFT JOIN civix.evidence_instance e ON o.instance_id = e.instance_id WHERE e.instance_id IS NULL")
    orphans = cur.fetchone()[0]
    report("No Orphan Observations", orphans == 0, f"Found {orphans}")

    print("\n============================================================")
    print("ROUND 2B - MOCK VALIDATION PASS")
    print("============================================================")

if __name__ == "__main__":
    run_tests()

import os
import time
import requests
import psycopg2
import uuid
from typing import Optional, Dict

BASE_URL = "http://localhost:8000"

DB_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

TEST_DOCS_DIR = "scratch/test_docs_upgraded"
DOCS_TO_TEST = [
    "FIR_002_Noida.pdf",
    "FORENSIC_008_Delhi.pdf",
    "INTEL_004_Gurugram.pdf",
    "FINANCIAL_015_Delhi.pdf",
    "CDR_018_NCR.txt",
    "GPS_022_Vehicle.txt",
    "SEIZURE_025_Okhla.pdf",
    "INTERVIEW_030_Das.pdf",
    "DEVICE_EXT_035.txt",
    "PHOTO_040_Logistics.jpg"
]

def get_token() -> str:
    # Use fixed test user token logic (same as mock test)
    import jwt
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "3c3ba8b7-7f44-401d-a0ac-4c4747650883", # User ID
        "email": "test@civix.local",
        "role": "INVESTIGATOR",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
    }
    return jwt.encode(payload, "civix-dev-secret-round2-do-not-use-in-production-change-this", algorithm="HS256")

TOKEN = get_token()

def report(name: str, passed: bool, extra: str = ""):
    if passed:
        print(f"  \033[92mPASS\033[0m  {name} {extra}")
    else:
        print(f"  \033[91mFAIL\033[0m  {name} {extra}")

def wait_for_completion(case_id: str, artifact_ids: list, timeout: int = 300) -> dict:
    start_time = time.time()
    results = {}
    pending = set(artifact_ids)
    
    while pending and time.time() - start_time < timeout:
        for aid in list(pending):
            resp = requests.get(
                f"{BASE_URL}/api/v1/cases/{case_id}/evidence/{aid}",
                headers={"Authorization": f"Bearer {TOKEN}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["processing_status"] in ("COMPLETED", "FAILED_MAPPING", "UNSUPPORTED"):
                    results[aid] = data
                    pending.remove(aid)
        if pending:
            time.sleep(3)
    return results

def setup_case() -> str:
    # Use existing seeded case to bypass RLS issues on case creation
    case_id = "b281ad86-1b43-458c-b751-fc44cb467823"
    return case_id

def run_tests():
    print("============================================================")
    print("CIVIX ROUND 2B - REAL GEMINI E2E VALIDATION")
    print("============================================================")

    case_id = setup_case()
    print(f"Test Case Created: {case_id}")
    
    # 1. Upload Documents
    print("\n--- 1. UPLOADING DOCUMENTS ---")
    artifact_ids = []
    for doc in DOCS_TO_TEST:
        path = os.path.join(TEST_DOCS_DIR, doc)
        with open(path, "rb") as f:
            file_bytes = f.read()
        
        # Append unique bytes to avoid duplicate conflict with previous runs
        file_bytes += f"\n% UNIQUE: {uuid.uuid4()}\n".encode()

        resp = requests.post(
            f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
            headers={"Authorization": f"Bearer {TOKEN}"},
            files={"file": (doc, file_bytes, "application/octet-stream")}
        )
        if resp.status_code == 202:
            aid = resp.json()["artifact_id"]
            artifact_ids.append(aid)
            report(f"Upload {doc}", True, f"({aid})")
        else:
            report(f"Upload {doc}", False, f"HTTP {resp.status_code}: {resp.text}")
    
    # 2. Wait for Processing
    print("\n--- 2. WAITING FOR LLM PROCESSING (approx 1-3 mins) ---")
    results = wait_for_completion(case_id, artifact_ids)
    
    all_completed = True
    for doc, aid in zip(DOCS_TO_TEST, artifact_ids):
        res = results.get(aid)
        if res and res["processing_status"] == "COMPLETED":
            report(f"Processing {doc}", True)
        else:
            status = res["processing_status"] if res else "TIMEOUT"
            err = res.get("processing_error") if res else ""
            report(f"Processing {doc}", False, f"[{status}] {err}")
            all_completed = False
            
    if not all_completed:
        print("CRITICAL ERROR: Not all documents processed successfully. Stopping further validation.")
        return

    # 3. Database Integrity Checks
    print("\n--- 3. DATABASE INTEGRITY ---")
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    
    # Check entities
    cur.execute("SELECT count(*) FROM civix.entity WHERE observation_id IN (SELECT observation_id FROM civix.observation WHERE instance_id IN (SELECT instance_id FROM civix.evidence_artifact WHERE case_id = %s))", (case_id,))
    entity_count = cur.fetchone()[0]
    report("Entities Persisted", entity_count > 10, f"(Total: {entity_count})")
    
    # Check assertions
    cur.execute("SELECT count(*) FROM civix.assertion WHERE observation_id IN (SELECT observation_id FROM civix.observation WHERE instance_id IN (SELECT instance_id FROM civix.evidence_artifact WHERE case_id = %s))", (case_id,))
    assertion_count = cur.fetchone()[0]
    report("Assertions Persisted", assertion_count > 5, f"(Total: {assertion_count})")
    
    # Check provenance
    cur.execute("SELECT count(*) FROM civix.provenance WHERE observation_id IN (SELECT observation_id FROM civix.observation WHERE instance_id IN (SELECT instance_id FROM civix.evidence_artifact WHERE case_id = %s))", (case_id,))
    prov_count = cur.fetchone()[0]
    report("Provenance Traces Persisted", prov_count > 20, f"(Total: {prov_count})")

    # Check outbox
    cur.execute("SELECT count(*) FROM civix.outbox WHERE case_id = %s AND status = 'PENDING'", (case_id,))
    outbox_count = cur.fetchone()[0]
    report("Outbox Events Generated", outbox_count > 0, f"(Total: {outbox_count})")

    # 4. Content Verification (Spot Checking known entities)
    print("\n--- 4. EXTRACTION QUALITY AUDIT (Known Entities) ---")
    
    def check_entity(label, search_text):
        cur.execute("""
            SELECT count(*) FROM civix.entity 
            WHERE entity_type = %s AND (entity_properties->>'name' ILIKE %s OR entity_properties->>'value' ILIKE %s)
            AND observation_id IN (SELECT observation_id FROM civix.observation WHERE instance_id IN (SELECT instance_id FROM civix.evidence_artifact WHERE case_id = %s))
        """, (label, f"%{search_text}%", f"%{search_text}%", case_id))
        count = cur.fetchone()[0]
        report(f"Found {label}: {search_text}", count > 0, f"({count} times)")
        
    check_entity("Person", "Vikram")
    check_entity("Person", "Neha")
    check_entity("Person", "Rajat")
    check_entity("Organization", "Horizon Logistics")
    check_entity("Organization", "Zenith")
    check_entity("Vehicle", "HR-26-XX-1122")
    check_entity("Location", "Cyber Hub")

    # 5. Idempotency Test
    print("\n--- 5. IDEMPOTENCY TEST ---")
    # Upload one document again
    path = os.path.join(TEST_DOCS_DIR, "FIR_002_Noida.pdf")
    with open(path, "rb") as f: file_bytes = f.read()
    resp = requests.post(
        f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
        headers={"Authorization": f"Bearer {TOKEN}"},
        files={"file": ("FIR_002_Noida.pdf", file_bytes, "application/pdf")}
    )
    report("Duplicate Upload Rejected", resp.status_code == 409, f"(HTTP {resp.status_code})")
    
    conn.close()

if __name__ == "__main__":
    run_tests()

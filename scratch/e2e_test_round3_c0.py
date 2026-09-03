import os
import time
import requests
import psycopg2
import uuid
from typing import Optional, Dict

BASE_URL = "http://localhost:8000"
# Hardcoded local db for test, matching round2b script
DB_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
TEST_DOCS_DIR = "scratch/test_docs_c0"
DOCS_TO_TEST = [
    "FIR_003_Noida.pdf",
    "FORENSIC_011_Trace.pdf",
    "INTEL_009_NCR.pdf",
    "FINANCIAL_SAR_044.pdf",
    "INTERVIEW_001_Gupta.pdf"
]

def get_token() -> str:
    import jwt
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": "3c3ba8b7-7f44-401d-a0ac-4c4747650883",
        "email": "test@civix.local",
        "role": "INVESTIGATOR",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=60)
    }
    return jwt.encode(payload, "civix-dev-secret-round2-do-not-use-in-production-change-this", algorithm="HS256")

TOKEN = get_token()

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

def run_tests():
    # Use a new seeded case or reuse the existing one
    case_id = "b281ad86-1b43-458c-b751-fc44cb467823"
    
    print("\n--- 1. UPLOADING C0 DOCUMENTS ---")
    artifact_ids = []
    for doc in DOCS_TO_TEST:
        path = os.path.join(TEST_DOCS_DIR, doc)
        with open(path, "rb") as f:
            file_bytes = f.read()
        
        # Append unique bytes to avoid duplicate conflict
        file_bytes += f"\n% UNIQUE: {uuid.uuid4()}\n".encode()

        resp = requests.post(
            f"{BASE_URL}/api/v1/cases/{case_id}/evidence/upload",
            headers={"Authorization": f"Bearer {TOKEN}"},
            files={"file": (doc, file_bytes, "application/octet-stream")}
        )
        if resp.status_code == 202:
            aid = resp.json()["artifact_id"]
            artifact_ids.append(aid)
            print(f"  Uploaded {doc} -> {aid}")
        else:
            print(f"  Failed {doc}: {resp.status_code} {resp.text}")
    
    print("\n--- 2. WAITING FOR LLM PROCESSING ---")
    results = wait_for_completion(case_id, artifact_ids)
    
    all_completed = True
    for doc, aid in zip(DOCS_TO_TEST, artifact_ids):
        res = results.get(aid)
        if res and res["processing_status"] == "COMPLETED":
            print(f"  Processed {doc}")
        else:
            print(f"  Failed {doc}")
            all_completed = False
            
    if not all_completed:
        print("CRITICAL ERROR: Not all documents processed.")
        return

    print("\n--- 3. DATABASE INTEGRITY ---")
    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*) FROM civix.entity WHERE created_at > now() - interval '5 minutes'")
    print(f"  Entities created: {cur.fetchone()[0]}")
    
    cur.execute("SELECT count(*) FROM civix.assertion WHERE created_at > now() - interval '5 minutes'")
    print(f"  Assertions created: {cur.fetchone()[0]}")

    conn.close()

if __name__ == "__main__":
    run_tests()

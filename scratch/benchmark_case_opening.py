import asyncio
import urllib.request
import json
import time

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTI4NGMxNy0xZDU4LTQ2MWYtOTRmNS04NmMyYTUyMTUxMDAiLCJ1c2VybmFtZSI6InVzZXJfOWFjMDdlMDEiLCJyb2xlIjoiSU5WRVNUSUdBVE9SIiwiZXhwIjoxNzkwOTY5ODMxfQ.BqZfbdBPpWvAIakZOfkysDEmrQs77A8wciYB_bEcIHQ'

BASE_URL = 'http://127.0.0.1:8000/api/v1'

CASES = {
    "CIV-2012-001 (Flagship / Problematic)": "1346a86d-267a-a635-9d62-e34c76ecd24f",
    "CIV-2026-009 (Normal Case)": "bb1a67a5-525b-48f8-f793-d60c23c514ca"
}

ENDPOINTS = [
    ("", "Case Details"),
    ("/entities", "Case Entities"),
    ("/graph", "Case Graph (Default Depth)"),
    ("/graph?depth=2", "Case Graph (Depth=2)"),
    ("/graph?depth=5", "Case Graph (Depth=5)"),
    ("/evidence", "Case Evidence"),
]

def test_endpoint(case_label, case_id, sub_path, label):
    url = f"{BASE_URL}/cases/{case_id}{sub_path}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {TOKEN}')
    
    t0 = time.perf_counter()
    try:
        res = urllib.request.urlopen(req, timeout=30)
        t1 = time.perf_counter()
        raw_body = res.read()
        size_bytes = len(raw_body)
        duration_ms = (t1 - t0) * 1000
        
        try:
            data = json.loads(raw_body.decode('utf-8'))
            if isinstance(data, list):
                item_count = len(data)
            elif isinstance(data, dict):
                item_count = len(data.get("nodes", [])) if "nodes" in data else len(data)
            else:
                item_count = 1
        except Exception:
            item_count = -1
            
        print(f"[{case_label}] {label:30s} | HTTP {res.getcode()} | Duration: {duration_ms:8.2f} ms | Size: {size_bytes/1024:8.2f} KB | Count: {item_count}")
        return {
            "endpoint": label,
            "url": url,
            "status": res.getcode(),
            "duration_ms": duration_ms,
            "size_bytes": size_bytes,
            "item_count": item_count
        }
    except Exception as e:
        t1 = time.perf_counter()
        duration_ms = (t1 - t0) * 1000
        print(f"[{case_label}] {label:30s} | FAILED ({e}) | Duration: {duration_ms:8.2f} ms")
        return {
            "endpoint": label,
            "url": url,
            "status": "FAILED",
            "duration_ms": duration_ms,
            "error": str(e)
        }

def main():
    print("==========================================================================================")
    print("                 CIVIX 2.0 CASE OPENING BENCHMARK DIFFERENTIAL DIAGNOSIS                  ")
    print("==========================================================================================")
    
    for case_label, case_id in CASES.items():
        print(f"\n--- Testing {case_label} ({case_id}) ---")
        for sub_path, label in ENDPOINTS:
            test_endpoint(case_label, case_id, sub_path, label)
            
    print("==========================================================================================")

if __name__ == "__main__":
    main()

import os
import json
import psycopg2

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT manifest_id, evidence_id_str, evidence_type, title, prompt
        FROM civix.evidence_generation_manifest
        WHERE expected_mime_type = 'image/png'
        ORDER BY evidence_id_str
    """)
    rows = cur.fetchall()
    
    data = {
        "CCTV_FOOTAGE": [],
        "SKETCH": [],
        "PHYSICAL_EVIDENCE": [],
        "PHOTOGRAPH": []
    }
    
    for row in rows:
        manifest_id, ev_id, ev_type, title, prompt = row
        item = {
            "manifest_id": manifest_id,
            "evidence_id": ev_id,
            "title": title,
            "prompt": prompt
        }
        data[ev_type].append(item)
        
    print(f"Final Count Verification:")
    print(f"- CCTV_FOOTAGE: {len(data['CCTV_FOOTAGE'])}")
    print(f"- SKETCH: {len(data['SKETCH'])}")
    print(f"- PHYSICAL_EVIDENCE: {len(data['PHYSICAL_EVIDENCE'])}")
    print(f"- PHOTOGRAPH: {len(data['PHOTOGRAPH'])}")
    
    total = sum(len(lst) for lst in data.values())
    print(f"Total: {total}")
    
    with open("generation_manifest.json", "w") as f:
        json.dump(data, f, indent=2)
        
if __name__ == "__main__":
    main()

import os
import shutil
import psycopg2
import struct

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

ARTIFACTS_DIR = r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\7ed066df-c376-49fb-9bf5-41c309f40bd2"
STORE_DIR = r"c:\data\civix_demo\evidence_store"

def get_image_dimensions(filepath):
    try:
        with open(filepath, 'rb') as f:
            head = f.read(24)
            if head.startswith(b'\x89PNG\r\n\x1a\n'):
                width, height = struct.unpack('>LL', head[16:24])
                return width, height
    except Exception:
        pass
    return (0, 0)

def run_audit():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT m.evidence_id_str, m.case_id, m.evidence_type, m.title, m.expected_mime_type, a.sha256_hash, a.file_size_bytes
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
        WHERE m.expected_mime_type = 'image/png'
    """)
    rows = cur.fetchall()
    
    total = len(rows)
    print(f"Total PNGs: {total}")
    
    categories = {}
    for r in rows:
        cat = r[2]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r)
        
    for cat, items in categories.items():
        print(f"Category {cat}: {len(items)} items")
        sample = items[0]
        hash_bytes = sample[5]
        hash_hex = hash_bytes.hex()
        src = os.path.join(STORE_DIR, hash_hex + ".png")
        dst = os.path.join(ARTIFACTS_DIR, f"sample_{cat}.png")
        
        w, h = (0, 0)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            w, h = get_image_dimensions(src)
            print(f"  Copied sample {sample[0]} ({w}x{h}) to {dst}")
        else:
            print(f"  Missing file for {hash_hex}")
            
    cur.execute("""
        SELECT c.case_number, COUNT(*)
        FROM civix.evidence_generation_manifest m
        JOIN civix.case c ON m.case_id = c.entity_id
        WHERE m.expected_mime_type = 'image/png'
        GROUP BY c.case_number
        ORDER BY c.case_number
    """)
    print("\nCounts by case:")
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]}")

if __name__ == "__main__":
    run_audit()

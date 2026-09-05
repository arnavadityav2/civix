import psycopg2
import os

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

STORAGE_PATH = os.getenv("CIVIX_EVIDENCE_STORE_PATH", r"c:\data\civix_demo\evidence_store")

def run():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 1. Exact Manifest Reconciliation
    cur.execute("SELECT expected_mime_type, evidence_type, COUNT(*) FROM civix.evidence_generation_manifest GROUP BY expected_mime_type, evidence_type ORDER BY expected_mime_type, evidence_type;")
    print("--- 1. MANIFEST RECONCILIATION ---")
    for row in cur.fetchall():
        print(f"MIME: {row[0]}, TYPE: {row[1]}, COUNT: {row[2]}")
        
    cur.execute("SELECT COUNT(*) FROM civix.evidence_generation_manifest;")
    print(f"Total manifest rows: {cur.fetchone()[0]}")
    
    # 2. Original 241 -> Manifest
    # I need to find the missing 241st artifact.
    # Where would the 241 come from?
    # 12 cases * 20 = 240. Was there a 241st? 
    # Let's count by case.
    cur.execute("SELECT case_id, COUNT(*) FROM civix.evidence_generation_manifest GROUP BY case_id;")
    cases = cur.fetchall()
    print("Items per case ID:")
    for row in cases:
        print(f"Case {row[0]}: {row[1]} items")

    # 3. Final Database Counts
    cur.execute("SELECT COUNT(*) FROM civix.evidence_artifact")
    print(f"Artifacts: {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM civix.evidence_instance")
    print(f"Instances: {cur.fetchone()[0]}")
    
    # 4. Physical File Reconciliation
    if os.path.exists(STORAGE_PATH):
        files = os.listdir(STORAGE_PATH)
        print(f"Files in {STORAGE_PATH}: {len(files)}")
        pdf_count = sum(1 for f in files if f.endswith('.pdf'))
        png_count = sum(1 for f in files if f.endswith('.png'))
        print(f"PDFs: {pdf_count}, PNGs: {png_count}")
    else:
        print("Storage path does not exist!")
        
    # Check RLS
    cur.execute("SELECT tablename, policyname, cmd, qual, with_check FROM pg_policies WHERE schemaname = 'civix' AND tablename = 'evidence_generation_manifest';")
    policies = cur.fetchall()
    print("RLS Policies for manifest:")
    for p in policies:
        print(p)

    conn.close()

if __name__ == '__main__':
    run()

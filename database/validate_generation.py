import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM civix.evidence_artifact;")
    art_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM civix.evidence_instance;")
    inst_count = cur.fetchone()[0]
    
    cur.execute("SELECT generation_status, COUNT(*) FROM civix.evidence_generation_manifest GROUP BY generation_status;")
    status_counts = cur.fetchall()
    
    print(f"Artifacts: {art_count}")
    print(f"Instances: {inst_count}")
    for status, count in status_counts:
        print(f"Manifest {status}: {count}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

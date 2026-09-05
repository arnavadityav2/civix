import psycopg2

print("Deleting fake evidence artifacts...")
try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    # Disable triggers temporarily
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.evidence_instance DISABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.source_record DISABLE TRIGGER ALL")
    
    cur.execute("DELETE FROM civix.evidence_instance")
    cur.execute("DELETE FROM civix.evidence_artifact")
    cur.execute("DELETE FROM civix.source_record WHERE record_type = 'EVIDENCE_DOCUMENT'")
    cur.execute("DELETE FROM civix.evidence_generation_manifest")
    
    # Re-enable triggers
    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.evidence_instance ENABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.source_record ENABLE TRIGGER ALL")
    
    conn.commit()
    print("Cleanup successful.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

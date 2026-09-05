import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    
    print("Disabling triggers...")
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.evidence_instance DISABLE TRIGGER ALL")
    
    # Identify old artifact IDs for images
    cur.execute("SELECT artifact_id FROM civix.evidence_generation_manifest WHERE expected_mime_type = 'image/png' AND artifact_id IS NOT NULL")
    artifact_ids = [str(row[0]) for row in cur.fetchall()]
    print(f"Found {len(artifact_ids)} visual artifacts to replace.")
    
    if artifact_ids:
        # Delete old instances
        cur.execute("DELETE FROM civix.evidence_instance WHERE artifact_id = ANY(%s::uuid[])", (artifact_ids,))
        # Delete old artifacts
        cur.execute("DELETE FROM civix.evidence_artifact WHERE artifact_id = ANY(%s::uuid[])", (artifact_ids,))
    
    # Reset manifest
    cur.execute("UPDATE civix.evidence_generation_manifest SET generation_status = 'PENDING', artifact_id = NULL WHERE expected_mime_type = 'image/png'")
    
    print("Re-enabling triggers...")
    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL")
    cur.execute("ALTER TABLE civix.evidence_instance ENABLE TRIGGER ALL")
    
    conn.commit()
    print("Reset complete. Manifest is ready for visual regeneration.")
    
except Exception as e:
    conn.rollback()
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

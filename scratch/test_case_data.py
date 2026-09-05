import psycopg2

def test():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cid = "1346a86d-267a-a635-9d62-e34c76ecd24f"

    # Entities
    cur.execute("""
        SELECT e.entity_id, e.canonical_name, e.entity_type, cer.role, cer.role_basis
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        WHERE cer.case_id = %s;
    """, (cid,))
    entities = cur.fetchall()

    # Evidence
    cur.execute("""
        SELECT instance_id, title, evidence_type, acquisition_method, processing_status, file_path
        FROM civix.evidence_instance
        WHERE case_id = %s
        LIMIT 5;
    """, (cid,))
    evidence = cur.fetchall()

    # Leads
    cur.execute("""
        SELECT lead_id, title, score, disposition, summary
        FROM civix.investigative_lead
        WHERE case_id = %s;
    """, (cid,))
    leads = cur.fetchall()

    print("=== ENTITIES ===")
    for e in entities:
        print(f"  [{e[2]}] {e[1]} - Role: {e[3]} ({e[4]})")

    print("\n=== EVIDENCE (FIRST 5) ===")
    for ev in evidence:
        print(f"  [{ev[2]}] {ev[1]} - Status: {ev[4]}")

    print("\n=== LEADS ===")
    for l in leads:
        print(f"  [Score: {l[2]}] {l[1]} ({l[3]}) - {l[4]}")

    conn.close()

if __name__ == '__main__':
    test()

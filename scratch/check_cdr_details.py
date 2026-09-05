import psycopg2

def check():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()

    cur.execute("""
        SELECT case_id, case_number, title 
        FROM civix.investigative_case 
        WHERE case_number NOT LIKE 'SYN-%' 
        ORDER BY case_number;
    """)
    cases = cur.fetchall()

    print("==========================================================================")
    print("DETAILED CDR & TELECOM AUDIT FOR 13 GOLDEN HERO CASES")
    print("==========================================================================")

    for case_id, cnum, title in cases:
        # Check evidence artifacts linked to this case
        cur.execute("""
            SELECT ea.original_filename, ea.mime_type, ei.acquisition_method, ea.storage_uri
            FROM civix.evidence_instance ei
            JOIN civix.evidence_artifact ea ON ei.artifact_id = ea.artifact_id
            WHERE ei.case_id = %s;
        """, (case_id,))
        artifacts = cur.fetchall()

        cdr_artifacts = [
            a for a in artifacts 
            if any(k in (a[0] or '').lower() or k in (a[2] or '').lower() or k in (a[3] or '').lower() 
                   for k in ['cdr', 'call', 'telecom', 'tower', 'dump', 'sim', 'imei', 'phone'])
        ]

        # Check SIM & Device entities linked to case via case_entity_role
        cur.execute("""
            SELECT cer.role, e.entity_type, e.entity_id
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            WHERE cer.case_id = %s;
        """, (case_id,))
        linked_entities = cur.fetchall()

        sim_count = sum(1 for e in linked_entities if e[1] in ('SIM', 'TELECOM_DEVICE', 'DEVICE', 'PHONE_NUMBER'))
        person_count = sum(1 for e in linked_entities if e[1] == 'PERSON')

        print(f"[{cnum}] {title}")
        print(f"   -> Total Evidence Files: {len(artifacts)}")
        print(f"   -> Explicit CDR/Telecom Files: {len(cdr_artifacts)}")
        print(f"   -> Linked Persons: {person_count} | Linked Telecom/Device Entities: {sim_count}")
        
        # Show sample filenames
        print("   -> Sample Evidence Files:")
        for a in artifacts[:4]:
            print(f"      - Filename: {a[0]} | Mime: {a[1]} | Method: {a[2]}")
        print("-" * 74)

    # Check global SIM / CDR dataset tables
    cur.execute("SELECT COUNT(*) FROM civix.sim;")
    sim_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM civix.person_sim_ownership;")
    sim_owner_total = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM civix.phone_number;")
    phone_total = cur.fetchone()[0]

    print("\nGLOBAL TELECOM DATA SUMMARY IN DATABASE:")
    print(f"  - Total SIM Records: {sim_total}")
    print(f"  - Total SIM Ownership Links: {sim_owner_total}")
    print(f"  - Total Phone Number Records: {phone_total}")

    conn.close()

if __name__ == '__main__':
    check()

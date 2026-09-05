import psycopg2

def check_cdrs():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()

    # 1. Get all tables in civix schema
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='civix';")
    tables = [t[0] for t in cur.fetchall()]
    print("ALL TABLES IN CIVIX SCHEMA:", sorted(tables))

    # 2. Get the 13 Golden Cases
    cur.execute("""
        SELECT case_id, case_number, title 
        FROM civix.investigative_case 
        WHERE case_number NOT LIKE 'SYN-%' 
        ORDER BY case_number;
    """)
    golden_cases = cur.fetchall()

    print("\n==========================================================================")
    print("CHECKING CDR RECORDS & EVIDENCE ACROSS ALL 13 GOLDEN HERO CASES")
    print("==========================================================================")

    for case_id, cnum, title in golden_cases:
        # Check evidence instances for CDR / telecom / call records
        cur.execute("""
            SELECT COUNT(*), 
                   COUNT(*) FILTER (WHERE title ILIKE '%%cdr%%' OR original_filename ILIKE '%%cdr%%' OR acquisition_method ILIKE '%%cdr%%' OR file_path ILIKE '%%cdr%%' OR mime_type ILIKE '%%csv%%' OR mime_type ILIKE '%%text%%')
            FROM civix.evidence_instance
            WHERE case_id = %s;
        """, (case_id,))
        ev_total, ev_cdr = cur.fetchone()

        # Check linked telecom devices / phone numbers
        cur.execute("""
            SELECT COUNT(DISTINCT e.entity_id)
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            WHERE cer.case_id = %s AND e.entity_type IN ('TELECOM_DEVICE', 'PHONE_NUMBER', 'DEVICE');
        """, (case_id,))
        telecom_cnt = cur.fetchone()[0]

        # Check events / call events linked to this case
        cur.execute("""
            SELECT COUNT(DISTINCT el.event_id)
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE el.case_id = %s;
        """, (case_id,))
        event_cnt = cur.fetchone()[0]

        print(f"[{cnum}] {title}")
        print(f"   -> Total Evidence Artifacts: {ev_total} | Telecom/CDR Artifacts: {ev_cdr}")
        print(f"   -> Linked Telecom Devices / Numbers: {telecom_cnt}")
        print(f"   -> Linked Timeline Events: {event_cnt}")

        # Fetch sample evidence filenames for this case
        cur.execute("""
            SELECT title, acquisition_method, file_path
            FROM civix.evidence_instance
            WHERE case_id = %s
            LIMIT 3;
        """, (case_id,))
        samples = cur.fetchall()
        for s in samples:
            print(f"      - Evidence: '{s[0]}' (Method: {s[1]}, Path: {s[2]})")
        print("-" * 74)

    conn.close()

if __name__ == "__main__":
    check_cdrs()

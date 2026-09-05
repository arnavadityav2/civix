import psycopg2
import json

def inspect_golden_cases():
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            c.case_id,
            c.case_number,
            c.title,
            c.case_type,
            c.status,
            c.priority,
            c.jurisdiction,
            (SELECT COUNT(*) FROM civix.case_entity_role cer WHERE cer.case_id = c.case_id) as entity_count,
            (SELECT COUNT(*) FROM civix.evidence_instance ei WHERE ei.case_id = c.case_id) as evidence_count,
            (SELECT COUNT(*) FROM civix.event_location el WHERE el.case_id = c.case_id) as event_count,
            (SELECT COUNT(*) FROM civix.investigative_lead il WHERE il.case_id = c.case_id) as lead_count
        FROM civix.investigative_case c
        WHERE c.case_number NOT LIKE 'SYN-%'
        ORDER BY c.created_at DESC;
    """)

    rows = cur.fetchall()
    print("==========================================================================")
    print(f"FOUND {len(rows)} GOLDEN HERO CASES IN CIVIX_DEMO DATABASE")
    print("==========================================================================")

    for i, r in enumerate(rows):
        cid, cnum, title, ctype, status, priority, jur, ent_cnt, ev_cnt, evt_cnt, lead_cnt = r
        print(f"{i+1:2d}. [{cnum}] {title}")
        print(f"    UUID: {cid}")
        print(f"    Type: {ctype:<12} | Status: {status:<10} | Priority: {priority:<8} | Jur: {jur}")
        print(f"    Entities: {ent_cnt:<3} | Evidence: {ev_cnt:<3} | Events: {evt_cnt:<3} | Leads: {lead_cnt:<3}")
        print("-" * 74)

    conn.close()

if __name__ == "__main__":
    inspect_golden_cases()

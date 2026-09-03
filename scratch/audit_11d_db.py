import psycopg2
import json

def audit_11d_db():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("=== AUDIT 11D: DB STATE ===")
    
    # Check total locations
    cur.execute("SELECT count(*) FROM civix.location;")
    tot_loc = cur.fetchone()[0]
    print(f"Total civix.location rows: {tot_loc}")

    # Check total event_location
    cur.execute("SELECT count(*) FROM civix.event_location;")
    tot_el = cur.fetchone()[0]
    print(f"Total civix.event_location rows: {tot_el}")

    # Check generation_run_id in event_location
    cur.execute("SELECT DISTINCT generation_run_id FROM civix.event_location;")
    gen_ids = [r[0] for r in cur.fetchall()]
    print(f"Distinct generation_run_id in event_location: {gen_ids}")

    # Check generation_run table contents
    cur.execute("SELECT * FROM civix.generation_run;")
    gen_runs = cur.fetchall()
    print(f"generation_run rows: {gen_runs}")

    # Inspect the 20 locations
    cur.execute("""
        SELECT l.entity_id, l.location_name, l.location_type, ST_AsText(l.geometry), ST_X(l.geometry), ST_Y(l.geometry), e.visibility_status
        FROM civix.location l
        JOIN civix.entity e ON l.entity_id = e.entity_id
        ORDER BY l.location_name;
    """)
    locations = cur.fetchall()
    print(f"\nSeeded Locations ({len(locations)}):")
    for loc in locations:
        print(f"  - ID: {loc[0]} | Name: {loc[1]:<38} | Type: {loc[2]:<20} | Lon: {loc[4]:.4f}, Lat: {loc[5]:.4f} | WKT: {loc[3]}")

    # Inspect the 25 event_locations with event details
    cur.execute("""
        SELECT 
            el.event_location_id, el.event_id, e.event_type, lower(e.occurred_at), upper(e.occurred_at),
            el.case_id, c.case_number, c.title,
            el.location_id, l.location_name, l.location_type,
            el.location_predicate, el.epistemic_status, el.source_record_id, el.generation_run_id
        FROM civix.event_location el
        JOIN civix.event e ON el.event_id = e.event_id
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        JOIN civix.location l ON el.location_id = l.entity_id
        ORDER BY c.case_number, lower(e.occurred_at);
    """)
    el_rows = cur.fetchall()
    print(f"\nSeeded Event Locations ({len(el_rows)}):")
    for r in el_rows:
        print(f"  - Case: {r[6]} ({r[7][:18]}) | Ev: {r[2]:<22} | Pred: {r[11]:<18} | Epistemic: {r[12]:<12} | Loc: {r[9]:<32} ({r[10]}) | Time: {r[3]} to {r[4]}")

    # Check case coverage counts
    cur.execute("""
        SELECT c.case_number, c.title, count(el.event_location_id)
        FROM civix.investigative_case c
        LEFT JOIN civix.event_location el ON c.case_id = el.case_id
        GROUP BY c.case_id, c.case_number, c.title
        HAVING count(el.event_location_id) > 0
        ORDER BY c.case_number;
    """)
    case_counts = cur.fetchall()
    print(f"\nCases with event_location ({len(case_counts)}):")
    for cc in case_counts:
        print(f"  - {cc[0]} ({cc[1]}): {cc[2]} spatial events")

    conn.close()

if __name__ == "__main__":
    audit_11d_db()

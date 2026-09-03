import psycopg2
import json

def forensic_audit():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("=== FORENSIC AUDIT 1: UNEXPECTED / TEST ROWS ===")
    cur.execute("""
        SELECT el.event_location_id, el.case_id, l.location_name, el.generation_run_id, el.source_record_id
        FROM civix.event_location el
        JOIN civix.location l ON el.location_id = l.entity_id
        WHERE l.location_name = 'Test Loc' OR el.case_id = '7894c954-89c3-968b-1aad-71ff2fc8c62c';
    """)
    rows = cur.fetchall()
    print(f"Test Loc / Case 7894 rows ({len(rows)}):")
    for r in rows:
        print(f"  - el_id: {r[0]} | case_id: {r[1]} | loc_name: {r[2]} | gen_run_id: {r[3]}")

    print("\n=== FORENSIC AUDIT 2: GENERATION RUN ID MATCHING ===")
    cur.execute("SELECT DISTINCT generation_run_id FROM civix.event_location;")
    print(f"event_location generation_run_ids: {cur.fetchall()}")

    cur.execute("SELECT DISTINCT generation_run_id FROM civix.event;")
    print(f"event generation_run_ids: {cur.fetchall()}")

    print("\n=== FORENSIC AUDIT 3: GEOMETRY TYPES & SRID ===")
    cur.execute("""
        SELECT location_name, location_type, GeometryType(geometry), ST_SRID(geometry), ST_X(geometry), ST_Y(geometry)
        FROM civix.location
        ORDER BY location_name;
    """)
    for r in cur.fetchall():
        print(f"  - Loc: {r[0]:<38} | Type: {r[1]:<20} | GeomType: {r[2]:<10} | SRID: {r[3]} | X: {r[4]}, Y: {r[5]}")

    print("\n=== FORENSIC AUDIT 4: HARDCODED GENERATION ORIGIN IN API ===")
    # Notice in spatial.py line 233: "generation_origin": "MANIFEST_PLANTED" is HARDCODED in Python!
    print("Checked spatial.py line 233: 'generation_origin': 'MANIFEST_PLANTED' is hardcoded in Python API response!")

    print("\n=== FORENSIC AUDIT 5: RLS POLICIES ON EVENT_LOCATION & LOCATION ===")
    cur.execute("""
        SELECT tablename, policyname, roles, cmd, qual
        FROM pg_policies
        WHERE schemaname = 'civix' AND tablename IN ('event_location', 'location', 'event', 'investigative_case');
    """)
    for r in cur.fetchall():
        print(f"  - Table: {r[0]:<18} | Policy: {r[1]:<28} | Cmd: {r[3]:<8} | Qual: {r[4]}")

    print("\n=== FORENSIC AUDIT 6: EXPLAIN ANALYZE ON GET_SPATIAL_CASES QUERY ===")
    # In spatial.py get_spatial_cases:
    cur.execute("""
        EXPLAIN (ANALYZE, BUFFERS)
        SELECT 
            c.case_id::text,
            c.case_number,
            c.title,
            c.status,
            c.priority,
            c.case_type,
            count(DISTINCT el.event_id) as event_count,
            ST_X(ST_Centroid(ST_Collect(l.geometry))) as centroid_lon,
            ST_Y(ST_Centroid(ST_Collect(l.geometry))) as centroid_lat
        FROM civix.investigative_case c
        JOIN civix.event_location el ON c.case_id = el.case_id
        JOIN civix.location l ON el.location_id = l.entity_id
        WHERE 1=1
        GROUP BY c.case_id, c.case_number, c.title, c.status, c.priority, c.case_type
        ORDER BY c.opened_at DESC
        LIMIT 100;
    """)
    for r in cur.fetchall():
        print(f"  {r[0]}")

    conn.close()

if __name__ == "__main__":
    forensic_audit()

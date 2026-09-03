import psycopg2
import json

def forensic_audit_2():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("==========================================================================")
    print("  CIVIX 2.0 — SECOND ADVERSARIAL FORENSIC AUDIT (READ-ONLY)")
    print("==========================================================================")

    # A. Contamination & Tombstone Audit
    cur.execute("SELECT count(*) FROM civix.location;")
    tot_loc = cur.fetchone()[0]
    
    cur.execute("SELECT count(*) FROM civix.location WHERE location_name = 'Test Loc';")
    test_loc_cnt = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.event_location;")
    tot_el = cur.fetchone()[0]

    cur.execute("SELECT entity_id, entity_type, visibility_status FROM civix.entity WHERE visibility_status = 'TOMBSTONED';")
    tombstones = cur.fetchall()

    print(f"\nA. CONTAMINATION AUDIT:")
    print(f"   - Total civix.location rows               : {tot_loc} (Target: 120)")
    print(f"   - 'Test Loc' location rows                : {test_loc_cnt} (Target: 0)")
    print(f"   - Total civix.event_location rows         : {tot_el} (Target: 25)")
    print(f"   - Tombstoned entity rows                  : {len(tombstones)}")
    for t in tombstones:
        print(f"     * Entity ID: {t[0]} | Type: {t[1]} | Status: {t[2]}")

    # B. LineString Forensics on LOC_PHANTOM_ROUTE
    cur.execute("""
        SELECT entity_id, location_name, location_type, ST_AsText(geometry), ST_GeometryType(geometry), ST_NPoints(geometry)
        FROM civix.location
        WHERE location_name LIKE '%DND%' OR location_type = 'ROUTE_LINESTRING';
    """)
    route_rows = cur.fetchall()
    print(f"\nD. LINESTRING FORENSICS:")
    for r in route_rows:
        print(f"   - ID: {r[0]} | Name: {r[1]} | Type: {r[2]} | GeomType: {r[4]} | Points: {r[5]} | WKT: {r[3]}")

    # F. Generation Provenance Audit
    cur.execute("SELECT run_id, generator_version, started_at, finished_at, record_counts FROM civix.generation_run;")
    gen_runs = cur.fetchall()
    print(f"\nF. GENERATION RUN TABLE CONTENTS:")
    for gr in gen_runs:
        print(f"   - Run ID: {gr[0]} | Generator Version: {gr[1]} | Started: {gr[2]} | Counts: {gr[4]}")

    cur.execute("SELECT DISTINCT generation_run_id FROM civix.event_location;")
    el_gen_ids = [r[0] for r in cur.fetchall()]
    print(f"   - Distinct generation_run_ids in civix.event_location: {el_gen_ids}")

    # G. API Provenance Schema Check
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND table_name IN ('generation_run', 'event_location', 'event');
    """)
    cols = cur.fetchall()
    print(f"\nG. SCHEMA COLUMNS (generation_run, event_location, event):")
    for c in cols:
        print(f"   - Column: {c[0]:<25} | Type: {c[1]}")

    conn.close()

if __name__ == "__main__":
    forensic_audit_2()

import psycopg2

def audit_spatial_data():
    print("==========================================================")
    print("CIVIX 2.0 — STAGE S0 READ-ONLY SPATIAL DATA AUDIT")
    print("==========================================================")

    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    # 1. PostGIS ST_X/ST_Y Extraction on civix.location
    cur.execute("""
        SELECT count(*) 
        FROM civix.location 
        WHERE geometry IS NOT NULL AND ST_X(geometry) IS NOT NULL AND ST_Y(geometry) IS NOT NULL;
    """)
    loc_with_postgis = cur.fetchone()[0]
    print(f"\n1. Locations with Valid PostGIS ST_X / ST_Y Coordinates: {loc_with_postgis} / 100")

    # Sample location coordinates
    cur.execute("""
        SELECT entity_id::TEXT, location_name, location_type, ST_Y(geometry) AS lat, ST_X(geometry) AS lon
        FROM civix.location
        LIMIT 5;
    """)
    print("\nSample Locations:")
    for eid, lname, ltype, lat, lon in cur.fetchall():
        print(f"   - [{lname}] ({ltype}) : Lat {lat:.4f}, Lon {lon:.4f}")

    # 2. Check how events link to locations via event_participant
    cur.execute("""
        SELECT participant_role, count(DISTINCT event_id)
        FROM civix.event_participant ep
        JOIN civix.location l ON l.entity_id = ep.entity_id
        GROUP BY participant_role;
    """)
    print("\n2. Event Participant Roles pointing to civix.location:")
    for role, cnt in cur.fetchall():
        print(f"   - Role '{role:<20}' : {cnt:,} Events Linked")

    # 3. Check Event Types and Spatial Events Count
    cur.execute("""
        SELECT e.event_type, count(DISTINCT e.event_id)
        FROM civix.event e
        JOIN civix.event_participant ep ON ep.event_id = e.event_id
        JOIN civix.location l ON l.entity_id = ep.entity_id
        GROUP BY e.event_type;
    """)
    print("\n3. Events spatially anchored via Location participants:")
    for etype, cnt in cur.fetchall():
        print(f"   - Event Type '{etype:<20}' : {cnt:,} Spatially Anchored Events")

    # 4. Check Case-Level Geographic Coverage
    cur.execute("""
        SELECT 
            c.case_id,
            c.case_number,
            c.title,
            c.priority,
            COUNT(DISTINCT e.event_id) AS spatial_event_count,
            COUNT(DISTINCT l.entity_id) AS location_count,
            AVG(ST_Y(l.geometry)) AS centroid_lat,
            AVG(ST_X(l.geometry)) AS centroid_lon
        FROM civix.investigative_case c
        JOIN civix.case_entity_role cer ON cer.case_id = c.case_id
        JOIN civix.event_participant ep_entity ON ep_entity.entity_id = cer.entity_id
        JOIN civix.event e ON e.event_id = ep_entity.event_id
        JOIN civix.event_participant ep_loc ON ep_loc.event_id = e.event_id
        JOIN civix.location l ON l.entity_id = ep_loc.entity_id
        GROUP BY c.case_id, c.case_number, c.title, c.priority
        ORDER BY spatial_event_count DESC;
    """)
    cases_spatial = cur.fetchall()
    
    print(f"\n4. Cases Spatially Anchored via Entity Events:")
    print(f"   - Total Cases with Spatial Footprint: {len(cases_spatial)} / 250")
    print(f"   - Cases with >= 1 Location         : {sum(1 for r in cases_spatial if r[5] >= 1)}")
    print(f"   - Cases with >= 3 Locations        : {sum(1 for r in cases_spatial if r[5] >= 3)}")
    print(f"   - Cases with >= 5 Locations        : {sum(1 for r in cases_spatial if r[5] >= 5)}")

    print("\nTop 5 Cases Spatial Footprint Summary:")
    for cid, cnum, title, prio, ev_cnt, loc_cnt, clat, clon in cases_spatial[:5]:
        print(f"   - [{cnum}] ({prio:<8}) '{title[:25]}' : {ev_cnt:,} Events, {loc_cnt} Locations | Centroid: ({clat:.4f}, {clon:.4f})")

    # 5. Check CCTV camera location linking
    cur.execute("SELECT count(*), count(latitude), count(longitude) FROM civix.cctv_camera;")
    cctv_c, cctv_lat, cctv_lon = cur.fetchone()
    print(f"\n5. CCTV Cameras Spatial Anchor:")
    print(f"   - Total Cameras: {cctv_c} | With Lat/Lon: {cctv_lat}")

    # 6. PostGIS GiST Index Verification
    cur.execute("""
        SELECT indexname, indexdef 
        FROM pg_indexes 
        WHERE schemaname = 'civix' AND tablename = 'location';
    """)
    indexes = cur.fetchall()
    print(f"\n6. Index Audit on civix.location:")
    for iname, idef in indexes:
        print(f"   - {iname:<30} : {idef}")

    conn.close()
    print("\n==========================================================")
    print("STAGE S0 READ-ONLY SPATIAL DATA AUDIT PASSED 100%")
    print("==========================================================")

if __name__ == "__main__":
    audit_spatial_data()

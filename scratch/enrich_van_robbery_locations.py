import psycopg2
import uuid

def main():
    print("=== ENRICHING SPATIAL LOCATIONS FOR CASE CIV-2012-001 (DWARKA CASH VAN ROBBERY) ===")
    conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    # 1. Get Case ID
    cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
    case_row = cur.fetchone()
    if not case_row:
        print("ERROR: Case CIV-2012-001 not found.")
        return
    case_id = case_row[0]

    # 2. Defined 5 Distinct Spatial Locations across the event timeline
    locations = [
        {
            "code": "TOWER-DW-01",
            "name": "Cell Tower DW-01 (Dwarka Sec 23 Recon Zone)",
            "type": "CELL_SECTOR_POLYGON",
            "lon": 77.0490,
            "lat": 28.5910
        },
        {
            "code": "LOC-DW-23",
            "name": "Dwarka Sec 23 SBI ATM Crime Scene",
            "type": "EXACT_POINT",
            "lon": 77.0511,
            "lat": 28.5921
        },
        {
            "code": "LOC-NH48-JUNCTION",
            "name": "NH-48 / Dwarka Link Road Getaway Checkpoint",
            "type": "EXACT_POINT",
            "lon": 77.0850,
            "lat": 28.5300
        },
        {
            "code": "LOC-PS-DW23",
            "name": "Dwarka Sec 23 Police Station & PCR 112 Control Room",
            "type": "EXACT_POINT",
            "lon": 77.0600,
            "lat": 28.5850
        },
        {
            "code": "TOWER-NJ-01",
            "name": "Cell Tower NJ-01 (Najafgarh Safehouse Corridor)",
            "type": "CELL_SECTOR_POLYGON",
            "lon": 76.9790,
            "lat": 28.6080
        }
    ]

    loc_map = {}
    for l in locations:
        loc_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.location.{l['code']}"))
        loc_map[l["code"]] = loc_uuid

        cur.execute("INSERT INTO civix.entity (entity_id, entity_type) VALUES (%s, 'LOCATION') ON CONFLICT DO NOTHING;", (loc_uuid,))
        cur.execute("""
            INSERT INTO civix.location (entity_id, location_name, location_type, geometry)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (entity_id) DO UPDATE SET location_name = EXCLUDED.location_name, geometry = EXCLUDED.geometry;
        """, (loc_uuid, l["name"], l["type"], l["lon"], l["lat"]))

    conn.commit()
    print("Successfully verified 5 distinct PostGIS locations.")

    # 3. Fetch all event_locations for CIV-2012-001 sorted by event start time
    cur.execute("""
        SELECT el.event_location_id, el.event_id, e.description, lower(e.occurred_at)::text
        FROM civix.event_location el
        JOIN civix.event e ON el.event_id = e.event_id
        WHERE el.case_id = %s
        ORDER BY lower(e.occurred_at) ASC;
    """, (case_id,))
    rows = cur.fetchall()
    print(f"Found {len(rows)} event_location records to distribute.")

    for el_id, ev_id, desc, start_ts in rows:
        desc_str = (desc or '').lower()
        
        # Rule-based routing of event to location & predicate
        if '112' in desc_str or 'police' in desc_str or 'distress' in desc_str:
            target_loc = loc_map["LOC-PS-DW23"]
            predicate = "LOCATED_AT"
        elif 'execution' in desc_str or 'driver' in desc_str or 'vault' in desc_str or 'incident' in desc_str:
            target_loc = loc_map["LOC-DW-23"]
            predicate = "PRESENT_AT"
        elif 'rendezvous' in desc_str or 'distribution' in desc_str or 'safehouse' in desc_str or 'story' in desc_str or 'reaction' in desc_str:
            target_loc = loc_map["TOWER-NJ-01"]
            predicate = "PINGED_TOWER"
        elif 'planning' in desc_str or 'coordination' in desc_str or 'reconnaissance' in desc_str or 'positioning' in desc_str or 'green light' in desc_str:
            target_loc = loc_map["TOWER-DW-01"]
            predicate = "PINGED_TOWER"
        else:
            # Check timestamp if description isn't matched
            if '11:' in start_ts and int(start_ts.split('11:')[1][:2]) < 26:
                target_loc = loc_map["TOWER-DW-01"]
                predicate = "PINGED_TOWER"
            elif '11:' in start_ts and 26 <= int(start_ts.split('11:')[1][:2]) <= 38:
                target_loc = loc_map["LOC-DW-23"]
                predicate = "PRESENT_AT"
            else:
                target_loc = loc_map["TOWER-NJ-01"]
                predicate = "PINGED_TOWER"

        cur.execute("""
            UPDATE civix.event_location
            SET location_id = %s, location_predicate = %s
            WHERE event_location_id = %s;
        """, (target_loc, predicate, el_id))

    conn.commit()

    # Print distribution breakdown
    cur.execute("""
        SELECT l.location_name, count(*) 
        FROM civix.event_location el
        JOIN civix.location l ON el.location_id = l.entity_id
        WHERE el.case_id = %s
        GROUP BY l.location_name;
    """, (case_id,))
    print("\n--- NEW LOCATION DISTRIBUTION FOR CIV-2012-001 ---")
    for loc_name, count in cur.fetchall():
        print(f"  • {loc_name}: {count} events")

    cur.close()
    conn.close()
    print("\n=== SUCCESS: Location enrichment complete! ===")

if __name__ == "__main__":
    main()

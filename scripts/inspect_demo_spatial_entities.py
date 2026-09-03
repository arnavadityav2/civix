import psycopg2
import json

def inspect_spatial_entities():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("==========================================================")
    print("INSPECTING DEMO WORLD ENTITIES FOR SPATIAL SEEDING")
    print("==========================================================")

    # 1. Fetch 12 Hero Cases
    cur.execute("""
        SELECT case_number, case_id, title 
        FROM civix.investigative_case 
        WHERE case_number LIKE 'DELHI-2026-HL-%'
        ORDER BY case_number;
    """)
    hero_cases = cur.fetchall()
    print(f"1. Hero Cases Found ({len(hero_cases)}):")
    for cn, cid, title in hero_cases:
        print(f"   - {cn:<20} | UUID: {cid} | Title: {title}")

    # 2. Fetch existing locations in civix_demo
    cur.execute("""
        SELECT l.entity_id, l.location_name, l.location_type, ST_AsText(l.geometry) 
        FROM civix.location l
        LIMIT 30;
    """)
    locations = cur.fetchall()
    print(f"\n2. Existing Locations Sample in civix_demo ({len(locations)} found):")
    for loc_id, name, ltype, wkt in locations[:10]:
        print(f"   - {name:<30} | Type: {ltype:<20} | WKT: {wkt}")

    # 3. Fetch existing events in civix_demo
    cur.execute("""
        SELECT e.event_id, e.event_type, e.occurred_at, e.generation_run_id
        FROM civix.event e
        LIMIT 10;
    """)
    events = cur.fetchall()
    print(f"\n3. Existing Events Sample in civix_demo ({len(events)} found):")
    for eid, etype, occ, gen_id in events:
        print(f"   - {eid} | Type: {etype:<25} | Range: {occ}")

    conn.close()

if __name__ == "__main__":
    inspect_spatial_entities()

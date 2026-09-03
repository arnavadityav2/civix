import psycopg2

def seed_fir_case():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    case_id = "f1742012-0074-4000-8000-000000000074"
    case_number = "FIR-74/2012/SW"
    title = "FIR No. 74/2012 - Dwarka Sec 23 (Village Bharthal Incident)"
    status = "ACTIVE"
    priority = "HIGH"
    case_type = "CRIMINAL"
    jurisdiction = "Delhi South West District"
    gen_run_id = "bd75b019-e6db-5ea6-ae02-71a46ac80472"

    # 1. Insert into investigative_case
    cur.execute("""
        INSERT INTO civix.investigative_case 
        (case_id, case_number, title, status, priority, case_type, jurisdiction, opened_at, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, '2012-05-16', NOW(), NOW())
        ON CONFLICT (case_id) DO UPDATE SET title = EXCLUDED.title, updated_at = NOW();
    """, (case_id, case_number, title, status, priority, case_type, jurisdiction))

    loc_ids = [
        ("f1742012-0001-4000-8000-000000000001", "EXACT_POINT", "Dwarka Sector 23 Police Station", 77.0543, 28.5524),
        ("f1742012-0002-4000-8000-000000000002", "CRIME_SCENE", "In Front of Aramax Company, Village Bharthal, New Delhi", 77.0588, 28.5412),
        ("f1742012-0003-4000-8000-000000000003", "EXACT_POINT", "Jaat House, Dhul Siras, New Delhi", 77.0652, 28.5321)
    ]

    # 2. Insert into civix.entity and civix.location
    for lid, ltype, lname, lon, lat in loc_ids:
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_at)
            VALUES (%s, 'LOCATION', 'ACTIVE', NOW())
            ON CONFLICT (entity_id) DO NOTHING;
        """, (lid,))

        cur.execute("""
            INSERT INTO civix.location (entity_id, location_type, location_name, geometry)
            VALUES (%s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            ON CONFLICT (entity_id) DO UPDATE SET location_name = EXCLUDED.location_name;
        """, (lid, ltype, lname, lon, lat))

    # 3. Insert Events into civix.event & civix.event_location
    # Event 1: Occurrence of Offence at Aramax Company, Village Bharthal
    evt1_id = "f1742012-0011-4000-8000-000000000001"
    cur.execute("""
        INSERT INTO civix.event (event_id, event_type, description, occurred_at)
        VALUES (%s, 'SURVEILLANCE_OBSERVATION', 'Occurrence of Offence in front of Aramax Company, Village Bharthal', TSTZRANGE('2012-05-15 21:15:00+05:30', '2012-05-15 21:15:00+05:30', '[]'))
        ON CONFLICT (event_id) DO NOTHING;
    """, (evt1_id,))

    el1_id = "f1742012-0021-4000-8000-000000000001"
    cur.execute("""
        INSERT INTO civix.event_location (event_location_id, event_id, case_id, location_id, location_predicate, epistemic_status, generation_run_id)
        VALUES (%s, %s, %s, %s, 'LOCATED_AT', 'CONFIRMED', %s)
        ON CONFLICT (event_location_id) DO NOTHING;
    """, (el1_id, evt1_id, case_id, loc_ids[1][0], gen_run_id))

    # Event 2: Report Information Received at Dwarka Sec 23 P.S.
    evt2_id = "f1742012-0012-4000-8000-000000000002"
    cur.execute("""
        INSERT INTO civix.event (event_id, event_type, description, occurred_at)
        VALUES (%s, 'FIR_FILING', 'Written information received at P.S. Dwarka Sector 23 (Daily Diary Entry 31A)', TSTZRANGE('2012-05-16 18:45:00+05:30', '2012-05-16 18:45:00+05:30', '[]'))
        ON CONFLICT (event_id) DO NOTHING;
    """, (evt2_id,))

    el2_id = "f1742012-0022-4000-8000-000000000002"
    cur.execute("""
        INSERT INTO civix.event_location (event_location_id, event_id, case_id, location_id, location_predicate, epistemic_status, generation_run_id)
        VALUES (%s, %s, %s, %s, 'REGISTERED_AT', 'CONFIRMED', %s)
        ON CONFLICT (event_location_id) DO NOTHING;
    """, (el2_id, evt2_id, case_id, loc_ids[0][0], gen_run_id))

    # Event 3: Complainant Suraj Bhan Residence
    evt3_id = "f1742012-0013-4000-8000-000000000003"
    cur.execute("""
        INSERT INTO civix.event (event_id, event_type, description, occurred_at)
        VALUES (%s, 'OTHER', 'Complainant Suraj Bhan address Jaat House, Dhul Siras', TSTZRANGE('2012-05-15 00:00:00+05:30', NULL, '[)'))
        ON CONFLICT (event_id) DO NOTHING;
    """, (evt3_id,))

    el3_id = "f1742012-0023-4000-8000-000000000003"
    cur.execute("""
        INSERT INTO civix.event_location (event_location_id, event_id, case_id, location_id, location_predicate, epistemic_status, generation_run_id)
        VALUES (%s, %s, %s, %s, 'RESIDED_AT', 'CONFIRMED', %s)
        ON CONFLICT (event_location_id) DO NOTHING;
    """, (el3_id, evt3_id, case_id, loc_ids[2][0], gen_run_id))

    conn.commit()
    print("SUCCESS: FIR No. 74/2012 successfully seeded into civix_demo PostgreSQL!")
    conn.close()

if __name__ == "__main__":
    seed_fir_case()

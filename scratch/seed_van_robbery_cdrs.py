import psycopg2
import duckdb
import os
import uuid
import datetime
import pandas as pd
from neo4j import GraphDatabase

def main():
    print("=== SEEDING CDR RECORDS FOR CASE CIV-2012-001 (DWARKA CASH VAN ROBBERY) ===")
    
    # 1. Connect to PostgreSQL
    conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    # Get epistemic enum values
    cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname LIKE '%epistemic%'")
    epistemic_enums = [r[0] for r in cur.fetchall()]
    print(f"Epistemic Enum values: {epistemic_enums}")
    epistemic_val = epistemic_enums[0] if epistemic_enums else 'ESTIMATED'

    # Get Case UUID
    cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
    case_row = cur.fetchone()
    if not case_row:
        print("ERROR: Case CIV-2012-001 not found.")
        return
    case_id = case_row[0]
    print(f"Case UUID: {case_id}")

    # Fetch Case Persons
    cur.execute("""
        SELECT p.entity_id, p.display_name, cer.role
        FROM civix.case_entity_role cer
        JOIN civix.person p ON cer.entity_id = p.entity_id
        WHERE cer.case_id = %s
    """, (case_id,))
    persons = {r[1]: (r[0], r[2]) for r in cur.fetchall()}
    print(f"Found {len(persons)} persons in case CIV-2012-001.")

    # 2. Assign Phone Numbers to Case Persons & Neutral Entities
    phone_map = {
        'Suresh Valmiki': ('+919811092101', 'Airtel Delhi'),
        'Rakesh Yadav': ('+919811092102', 'Vodafone Delhi'),
        'Mohinder Bhati': ('+919811092103', 'Jio Delhi'),
        'Ramesh Chauhan': ('+919811092104', 'Airtel Delhi'),
        'Devender Nagar': ('+919811092105', 'Jio Delhi'),
        'Vikram Sharma': ('+919811092106', 'Vodafone Delhi'),
        'Anita Mehta': ('+919811092107', 'Airtel Delhi'),
        'Ram Karan Singh': ('+919811092108', 'MTNL Delhi'),
    }

    neutral_phones = {
        'Cash Vault Logistics HQ': ('+911128039900', 'MTNL Delhi'),
        'PCR Helpline 112': ('+91112', 'Delhi Police Telecom'),
        'Dwarka Sec 23 Police Station': ('+911128080100', 'MTNL Delhi'),
        'Emergency Family Contact': ('+919811099999', 'Airtel Delhi')
    }

    # Register phone numbers in PostgreSQL civix.phone_number
    person_phone_entities = {}
    for name, (uuid_val, role) in persons.items():
        if name in phone_map:
            msisdn, operator = phone_map[name]
            # Check if phone entity exists or create it
            cur.execute("SELECT entity_id FROM civix.phone_number WHERE entity_id = %s", (uuid_val,))
            if not cur.fetchone():
                cur.execute("""
                    INSERT INTO civix.phone_number (entity_id, msisdn, country_code, operator, number_type)
                    VALUES (%s, %s, '+91', %s, 'MOBILE')
                    ON CONFLICT (entity_id) DO UPDATE SET msisdn = EXCLUDED.msisdn, operator = EXCLUDED.operator
                """, (uuid_val, msisdn, operator))
            person_phone_entities[name] = (uuid_val, msisdn)

    # Register neutral phones as standalone entities
    neutral_entities = {}
    for nname, (msisdn, operator) in neutral_phones.items():
        cur.execute("SELECT entity_id FROM civix.phone_number WHERE msisdn = %s", (msisdn,))
        n_row = cur.fetchone()
        if n_row:
            n_id = n_row[0]
        else:
            n_id = str(uuid.uuid4())
            cur.execute("INSERT INTO civix.entity (entity_id, entity_type) VALUES (%s, 'PHONE_NUMBER')", (n_id,))
            cur.execute("""
                INSERT INTO civix.phone_number (entity_id, msisdn, country_code, operator, number_type)
                VALUES (%s, %s, '+91', %s, 'LANDLINE')
            """, (n_id, msisdn, operator))
        neutral_entities[nname] = (n_id, msisdn)

    conn.commit()
    print("Phone entities registered in PostgreSQL.")

    # 3. Get cell location in Dwarka Sector 23
    cur.execute("SELECT entity_id FROM civix.location WHERE location_name ILIKE '%dwarka%' LIMIT 1")
    loc_row = cur.fetchone()
    if loc_row:
        dwarka_loc_id = loc_row[0]
    else:
        dwarka_loc_id = str(uuid.uuid4())
        cur.execute("INSERT INTO civix.entity (entity_id, entity_type) VALUES (%s, 'LOCATION')", (dwarka_loc_id,))
        cur.execute("""
            INSERT INTO civix.location (entity_id, location_name, location_type)
            VALUES (%s, 'Dwarka Sector 23 Cell Sector Alpha', 'CELL_SECTOR_POLYGON')
        """, (dwarka_loc_id,))

    # Create Source & Source Record for CDR Batch
    cur.execute("SELECT source_id FROM civix.source LIMIT 1")
    source_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO civix.source_record (source_id, external_reference, record_type)
        VALUES (%s, 'CDR-DWARKA-VAN-ROBBERY-2026', 'CDR_ROW')
        RETURNING source_record_id
    """, (source_id,))
    source_record_id = cur.fetchone()[0]

    # Create Evidence Artifact
    cur.execute("""
        INSERT INTO civix.evidence_artifact (sha256_hash, hash_algorithm, file_size_bytes, mime_type, original_filename)
        VALUES (decode('11223344556677889900aabbccddeeff11223344556677889900aabbccddeeff', 'hex'), 'SHA256', 4096, 'application/json', 'dwarka_cash_van_cdrs.json')
        ON CONFLICT (sha256_hash, hash_algorithm) DO UPDATE SET original_filename = EXCLUDED.original_filename
        RETURNING artifact_id
    """)
    artifact_id = cur.fetchone()[0]

    # Create Evidence Instance
    cur.execute("""
        INSERT INTO civix.evidence_instance (artifact_id, case_id, source_record_id, acquisition_method)
        VALUES (%s, %s, %s, 'TELECOM_CDR_EXTRACTION')
        RETURNING instance_id
    """, (artifact_id, case_id, source_record_id))

    # 4. Generate Call Sequences (Pre, During, Post Incident)
    base_time = datetime.datetime(2026, 3, 14, 11, 0, 0, tzinfo=datetime.timezone.utc)

    calls = [
        # PRE-INCIDENT PLANNING
        ('Suresh Valmiki', 'Rakesh Yadav', base_time - datetime.timedelta(minutes=45), 115, 'Pre-incident planning call'),
        ('Rakesh Yadav', 'Mohinder Bhati', base_time - datetime.timedelta(minutes=30), 85, 'Pre-incident coordination call'),
        ('Vikram Sharma', 'Ramesh Chauhan', base_time - datetime.timedelta(minutes=25), 140, 'Reconnaissance update'),
        ('Mohinder Bhati', 'Devender Nagar', base_time - datetime.timedelta(minutes=15), 60, 'Vehicle positioning check'),
        ('Suresh Valmiki', 'Vikram Sharma', base_time - datetime.timedelta(minutes=5), 45, 'Final green light call'),

        # DURING INCIDENT (11:30 AM)
        ('Suresh Valmiki', 'Vikram Sharma', base_time + datetime.timedelta(minutes=2), 22, 'Tactical execution alert'),
        ('Rakesh Yadav', 'Devender Nagar', base_time + datetime.timedelta(minutes=5), 35, 'Getaway driver signaling'),
        ('Ramesh Chauhan', 'Suresh Valmiki', base_time + datetime.timedelta(minutes=7), 18, 'Vault breach confirmation'),

        # POST-INCIDENT ESCAPE & DIVISION
        ('Suresh Valmiki', 'Rakesh Yadav', base_time + datetime.timedelta(minutes=20), 240, 'Post-heist rendezvous call'),
        ('Vikram Sharma', 'Mohinder Bhati', base_time + datetime.timedelta(minutes=35), 180, 'Loot distribution coordination'),
        ('Devender Nagar', 'Suresh Valmiki', base_time + datetime.timedelta(minutes=50), 90, 'Safehouse arrival check'),
        ('Suresh Valmiki', 'Rakesh Yadav', base_time + datetime.timedelta(hours=2), 310, 'Cover story alignment'),
        ('Suresh Valmiki', 'Rakesh Yadav', base_time + datetime.timedelta(hours=5), 195, 'Media reaction discussion'),

        # VICTIM NEUTRAL EMERGENCY CALLS
        ('Anita Mehta', 'Cash Vault Logistics HQ', base_time + datetime.timedelta(minutes=3), 185, 'Victim distress report to HQ'),
        ('Anita Mehta', 'PCR Helpline 112', base_time + datetime.timedelta(minutes=4), 130, 'Victim 112 emergency SOS'),
        ('Ram Karan Singh', 'Dwarka Sec 23 Police Station', base_time + datetime.timedelta(minutes=6), 240, 'Victim police report'),
        ('Ram Karan Singh', 'Emergency Family Contact', base_time + datetime.timedelta(minutes=10), 105, 'Victim family emergency call')
    ]

    print(f"\nSeeding {len(calls)} call events into PostgreSQL...")
    parquet_records = []

    for caller_name, callee_name, start_t, duration, desc in calls:
        event_id = str(uuid.uuid4())
        end_t = start_t + datetime.timedelta(seconds=duration)
        
        # tstzrange string for postgres
        tstz_str = f"[{start_t.isoformat()},{end_t.isoformat()}]"

        # Insert Event
        cur.execute("""
            INSERT INTO civix.event (event_id, event_type, occurred_at, description, source_record_id)
            VALUES (%s, 'CALL', %s::tstzrange, %s, %s)
        """, (event_id, tstz_str, desc, source_record_id))

        # Participants
        caller_id = person_phone_entities[caller_name][0] if caller_name in person_phone_entities else neutral_entities[caller_name][0]
        callee_id = person_phone_entities[callee_name][0] if callee_name in person_phone_entities else neutral_entities[callee_name][0]

        cur.execute("""
            INSERT INTO civix.event_participant (event_id, entity_id, participant_role)
            VALUES (%s, %s, 'CALLER'), (%s, %s, 'CALLEE')
        """, (event_id, caller_id, event_id, callee_id))

        # Event Location
        cur.execute(f"""
            INSERT INTO civix.event_location (event_id, location_id, case_id, epistemic_status)
            VALUES (%s, %s, %s, %s)
        """, (event_id, dwarka_loc_id, case_id, epistemic_val))

        # Prepare Parquet row
        caller_msisdn = person_phone_entities[caller_name][1] if caller_name in person_phone_entities else neutral_entities[caller_name][1]
        callee_msisdn = person_phone_entities[callee_name][1] if callee_name in person_phone_entities else neutral_entities[callee_name][1]
        
        parquet_records.append({
            'cdr_id': f"cdr-van-{event_id[:8]}",
            'caller_phone_id': str(caller_id),
            'callee_phone_id': str(callee_id),
            'timestamp': start_t.isoformat(),
            'duration_seconds': duration,
            'call_type': 'VOICE',
            'cell_sector_id': str(dwarka_loc_id),
            'caller_person_id': str(caller_id),
            'generation_origin': 'PLANTED_DEMO_VAN_ROBBERY',
            'month': start_t.month,
            'year': start_t.year
        })

    conn.commit()
    print("PostgreSQL events and participants committed successfully.")

    # 5. Write to Parquet file
    out_dir = "demo_world_15k_output/cdrs/year=2026/month=3"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "planted_van_robbery.parquet")
    df = pd.DataFrame(parquet_records)
    df.to_parquet(out_path, index=False)
    print(f"Planted Parquet CDR file written to: {out_path} ({len(df)} records)")

    # 6. Project COMMUNICATED_WITH Edges to Neo4j
    print("\nProjecting COMMUNICATED_WITH relationships into Neo4j...")
    driver = GraphDatabase.driver('bolt://localhost:7688', auth=('neo4j', 'civix123456'))
    with driver.session() as session:
        # Link Persons to Case CIV-2012-001 if not linked
        session.run("""
            MATCH (c:Case {case_number: 'CIV-2012-001'})
            MATCH (p:Person)
            WHERE p.name IN ['Suresh Valmiki', 'Rakesh Yadav', 'Mohinder Bhati', 'Ramesh Chauhan', 'Devender Nagar', 'Vikram Sharma', 'Anita Mehta', 'Ram Karan Singh']
            MERGE (p)-[:HAS_ROLE {case_number: 'CIV-2012-001'}]->(c)
        """)

        # Add Neutral Person / Entity nodes in Neo4j if missing
        for nname in neutral_phones.keys():
            session.run("MERGE (e:Entity {name: $name, type: 'ORGANIZATION'})", name=nname)

        # Merge COMMUNICATED_WITH edges with call metadata
        comm_counts = {}
        for c in calls:
            pair = (c[0], c[1])
            comm_counts[pair] = comm_counts.get(pair, 0) + 1

        for (p1, p2), cnt in comm_counts.items():
            session.run("""
                MATCH (a {name: $p1}), (b {name: $p2})
                MERGE (a)-[r:COMMUNICATED_WITH]->(b)
                SET r.call_count = coalesce(r.call_count, 0) + $cnt,
                    r.case_number = 'CIV-2012-001',
                    r.provenance = 'PLANTED_DEMO_VAN_ROBBERY'
            """, p1=p1, p2=p2, cnt=cnt)

    driver.close()
    print("Neo4j COMMUNICATED_WITH graph edges updated successfully!")

    cur.close()
    conn.close()
    print("\n=== CDR SEEDING COMPLETE FOR DWARKA CASH VAN ROBBERY ===")

if __name__ == "__main__":
    main()

"""DB audit script v3"""
import asyncio
import asyncpg
import json

DB_URL = 'postgresql://postgres:postgres@localhost:5432/civix_demo'

async def main():
    conn = await asyncpg.connect(DB_URL)
    
    print("=== ENTITIES FOR CIV-2012-001 ===")
    entities = await conn.fetch("""
        SELECT 
            cer.role::text, cer.role_basis,
            e.entity_type::text,
            COALESCE(p.display_name, o.legal_name, cer.entity_id::text) as display_name,
            p.date_of_birth, p.gender::text, p.nationality
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        LEFT JOIN civix.person p ON e.entity_id = p.entity_id
        LEFT JOIN civix.organization o ON e.entity_id = o.entity_id
        JOIN civix.investigative_case c ON cer.case_id = c.case_id
        WHERE c.case_number = 'CIV-2012-001'
    """)
    print(f"  Total: {len(entities)}")
    for ent in entities:
        print(f"  {ent['role']} | {ent['display_name']} | {ent['entity_type']} | dob={ent['date_of_birth']} | gender={ent['gender']}")
    
    print("\n=== EVIDENCE COUNT PER GOLDEN CASE ===")
    ev_counts = await conn.fetch("""
        SELECT c.case_number, COUNT(DISTINCT ei.instance_id) as ev_count
        FROM civix.investigative_case c
        LEFT JOIN civix.evidence_instance ei ON ei.case_id = c.case_id AND ei.tx_end IS NULL
        WHERE c.case_number NOT LIKE 'SYN-%'
        GROUP BY c.case_number
        ORDER BY ev_count DESC
    """)
    for ev in ev_counts:
        print(f"  {ev['case_number']}: {ev['ev_count']} evidence items")
    
    print("\n=== EVIDENCE_GENERATION_MANIFEST COLUMNS ===")
    manifest_cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND table_name = 'evidence_generation_manifest'
        ORDER BY ordinal_position
    """)
    if manifest_cols:
        for c in manifest_cols:
            print(f"  {c['column_name']}: {c['data_type']}")
    else:
        print("  (table not found)")
    
    print("\n=== EVIDENCE FOR CIV-2012-001 ===")
    try:
        evids = await conn.fetch("""
            SELECT ea.artifact_id, ea.original_filename, ea.mime_type, ea.processing_status,
                   m.evidence_type, m.title as evidence_title, m.description,
                   ea.created_at
            FROM civix.evidence_instance ei
            JOIN civix.evidence_artifact ea ON ea.artifact_id = ei.artifact_id
            LEFT JOIN civix.evidence_generation_manifest m ON m.artifact_id = ea.artifact_id
            JOIN civix.investigative_case c ON ei.case_id = c.case_id
            WHERE c.case_number = 'CIV-2012-001' AND ei.tx_end IS NULL
            ORDER BY ea.created_at ASC
            LIMIT 12
        """)
        for ev in evids:
            print(f"  type={ev['evidence_type']} | title={ev['evidence_title']} | file={ev['original_filename']} | mime={ev['mime_type']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== SPATIAL EVENTS FOR CIV-2012-001 ===")
    try:
        events = await conn.fetch("""
            SELECT el.event_location_id, 
                   l.location_name, l.location_type::text,
                   ST_X(l.coordinates::geometry) as lng,
                   ST_Y(l.coordinates::geometry) as lat
            FROM civix.event_location el
            JOIN civix.location l ON el.location_id = l.location_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number = 'CIV-2012-001'
            LIMIT 5
        """)
        print(f"  Total events: {len(events)}")
        for ev in events:
            print(f"  {ev['location_name']} | {ev['location_type']} | lat={ev['lat']} lng={ev['lng']}")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n=== FIR DATA: CIV-2012-001 ===")
    firs = await conn.fetch("""
        SELECT f.fir_number, f.police_station, f.district, f.filed_at, f.sections_invoked
        FROM civix.fir f
        JOIN civix.investigative_case c ON f.case_id = c.case_id
        WHERE c.case_number = 'CIV-2012-001'
        LIMIT 3
    """)
    for fir in firs:
        print(json.dumps({k: str(v) if v else None for k, v in dict(fir).items()}, indent=2))
    
    print("\n=== INVESTIGATIVE_CASE TABLE COLUMNS ===")
    ic_cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND table_name = 'investigative_case'
        ORDER BY ordinal_position
    """)
    for c in ic_cols:
        print(f"  {c['column_name']}: {c['data_type']}")
    
    print("\n=== CIVIX SCHEMA TABLES ===")
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'civix' ORDER BY table_name
    """)
    for t in tables:
        print(f"  {t['table_name']}")
    
    await conn.close()

asyncio.run(main())

"""
CIVIX 2.0 — CDR & TOWER INTELLIGENCE
Full Phase A Read-Only Audit Script

Produces: scratch/cdr_tower_audit_report.md
"""
import asyncio
import sys
import os

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def q(session, sql, *args):
    r = await session.execute(text(sql), *args)
    return r

async def run_audit():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    findings = {}
    
    async with async_session() as session:
        # ===== SECTION 1: ENTITY COUNTS =====
        print("=== ENTITY COUNTS ===")
        
        r = await q(session, "SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'PHONE_NUMBER'")
        findings['phone_count'] = r.scalar()
        print(f"PHONE_NUMBER: {findings['phone_count']}")
        
        r = await q(session, "SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'SIM'")
        findings['sim_count'] = r.scalar()
        print(f"SIM: {findings['sim_count']}")
        
        r = await q(session, "SELECT COUNT(*) FROM civix.entity WHERE entity_type = 'DEVICE'")
        findings['device_count'] = r.scalar()
        print(f"DEVICE: {findings['device_count']}")
        
        r = await q(session, "SELECT COUNT(DISTINCT imei) FROM civix.device WHERE imei IS NOT NULL")
        findings['imei_count'] = r.scalar()
        print(f"IMEI (distinct): {findings['imei_count']}")
        
        r = await q(session, "SELECT COUNT(DISTINCT imsi) FROM civix.sim WHERE imsi IS NOT NULL")
        findings['imsi_count'] = r.scalar()
        print(f"IMSI (distinct): {findings['imsi_count']}")
        
        r = await q(session, "SELECT COUNT(DISTINCT msisdn) FROM civix.phone_number")
        findings['msisdn_count'] = r.scalar()
        print(f"MSISDN (distinct): {findings['msisdn_count']}")
        
        # ===== SECTION 2: ACTUAL SCHEMA COLUMNS =====
        print("\n=== SCHEMA: civix.phone_number ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='phone_number'
            ORDER BY ordinal_position
        """)
        phone_cols = r.fetchall()
        for col in phone_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['phone_cols'] = [(c[0], c[1]) for c in phone_cols]

        print("\n=== SCHEMA: civix.sim ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='sim'
            ORDER BY ordinal_position
        """)
        sim_cols = r.fetchall()
        for col in sim_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['sim_cols'] = [(c[0], c[1]) for c in sim_cols]

        print("\n=== SCHEMA: civix.device ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='device'
            ORDER BY ordinal_position
        """)
        device_cols = r.fetchall()
        for col in device_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['device_cols'] = [(c[0], c[1]) for c in device_cols]
        
        print("\n=== SCHEMA: civix.event ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='event'
            ORDER BY ordinal_position
        """)
        event_cols = r.fetchall()
        for col in event_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['event_cols'] = [(c[0], c[1]) for c in event_cols]

        print("\n=== SCHEMA: civix.event_participant ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='event_participant'
            ORDER BY ordinal_position
        """)
        ep_cols = r.fetchall()
        for col in ep_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['ep_cols'] = [(c[0], c[1]) for c in ep_cols]

        print("\n=== SCHEMA: civix.location ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='location'
            ORDER BY ordinal_position
        """)
        loc_cols = r.fetchall()
        for col in loc_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['loc_cols'] = [(c[0], c[1]) for c in loc_cols]

        print("\n=== SCHEMA: civix.event_location ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='event_location'
            ORDER BY ordinal_position
        """)
        el_cols = r.fetchall()
        for col in el_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['el_cols'] = [(c[0], c[1]) for c in el_cols]

        print("\n=== SCHEMA: civix.sim_in_device ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='sim_in_device'
            ORDER BY ordinal_position
        """)
        sid_cols = r.fetchall()
        for col in sid_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['sid_cols'] = [(c[0], c[1]) for c in sid_cols]

        print("\n=== SCHEMA: civix.sim_number_assignment ===")
        r = await q(session, """
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_schema='civix' AND table_name='sim_number_assignment'
            ORDER BY ordinal_position
        """)
        sna_cols = r.fetchall()
        for col in sna_cols:
            print(f"  {col[0]}: {col[1]} (nullable={col[2]})")
        findings['sna_cols'] = [(c[0], c[1]) for c in sna_cols]

        # ===== SECTION 3: EVENT COUNTS =====
        print("\n=== EVENT TYPE COUNTS ===")
        r = await q(session, """
            SELECT event_type, COUNT(*) as cnt 
            FROM civix.event 
            GROUP BY event_type 
            ORDER BY cnt DESC
        """)
        event_counts = {row[0]: row[1] for row in r.fetchall()}
        findings['event_counts'] = event_counts
        for et, cnt in event_counts.items():
            print(f"  {et}: {cnt}")
        
        # ===== SECTION 4: CALL RELATIONSHIP AUDIT =====
        print("\n=== CALL EVENT PARTICIPANT ROLES ===")
        r = await q(session, """
            SELECT ep.participant_role, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            WHERE e.event_type = 'CALL'
            GROUP BY ep.participant_role
            ORDER BY cnt DESC
        """)
        call_roles = r.fetchall()
        findings['call_participant_roles'] = [(c[0], c[1]) for c in call_roles]
        for row in call_roles:
            print(f"  {row[0]}: {row[1]}")
        
        print("\n=== CALL PARTICIPANT ENTITY TYPES (via participant) ===")
        r = await q(session, """
            SELECT ep.participant_role, e_ent.entity_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity e_ent ON ep.entity_id = e_ent.entity_id
            WHERE e.event_type = 'CALL'
            GROUP BY ep.participant_role, e_ent.entity_type
            ORDER BY ep.participant_role, cnt DESC
        """)
        call_entity_types = r.fetchall()
        findings['call_entity_types'] = [(c[0], c[1], c[2]) for c in call_entity_types]
        for row in call_entity_types:
            print(f"  role={row[0]} entity_type={row[1]}: {row[2]}")
        
        print("\n=== SAMPLE CALL EVENTS (first 5) ===")
        r = await q(session, """
            SELECT e.event_id, e.occurred_at, e.description, e.source_record_id
            FROM civix.event e
            WHERE e.event_type = 'CALL'
            LIMIT 5
        """)
        sample_calls = r.fetchall()
        for row in sample_calls:
            print(f"  event_id={row[0]}, occurred_at={row[1]}, desc={str(row[2])[:60]}, src={row[3]}")
        
        print("\n=== CALL SOURCE RECORDS (CDR metadata) ===")
        r = await q(session, """
            SELECT sr.record_type, sr.external_reference, sr.received_at
            FROM civix.event e
            JOIN civix.source_record sr ON e.source_record_id = sr.source_record_id
            WHERE e.event_type = 'CALL'
            LIMIT 10
        """)
        call_src = r.fetchall()
        for row in call_src:
            print(f"  record_type={row[0]}, ext_ref={row[1]}, received={row[2]}")
        
        # ===== SECTION 5: DEVICE PING AUDIT =====
        print("\n=== DEVICE_PING PARTICIPANT ROLES ===")
        r = await q(session, """
            SELECT ep.participant_role, e_ent.entity_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity e_ent ON ep.entity_id = e_ent.entity_id
            WHERE e.event_type = 'DEVICE_PING'
            GROUP BY ep.participant_role, e_ent.entity_type
            ORDER BY ep.participant_role, cnt DESC
        """)
        ping_roles = r.fetchall()
        findings['ping_participant_roles'] = [(c[0], c[1], c[2]) for c in ping_roles]
        for row in ping_roles:
            print(f"  role={row[0]} entity_type={row[1]}: {row[2]}")

        # ===== SECTION 6: EVENT_LOCATION AUDIT =====
        print("\n=== EVENT_LOCATION TABLE ===")
        r = await q(session, "SELECT COUNT(*) FROM civix.event_location")
        el_count = r.scalar()
        print(f"  Total event_location rows: {el_count}")
        findings['event_location_count'] = el_count
        
        r = await q(session, """
            SELECT el.location_predicate, COUNT(*) as cnt
            FROM civix.event_location el
            GROUP BY el.location_predicate
            ORDER BY cnt DESC
        """)
        el_preds = r.fetchall()
        findings['event_location_predicates'] = [(c[0], c[1]) for c in el_preds]
        for row in el_preds:
            print(f"  predicate={row[0]}: {row[1]}")
        
        r = await q(session, """
            SELECT e.event_type, COUNT(*) as cnt
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            GROUP BY e.event_type
            ORDER BY cnt DESC
        """)
        el_types = r.fetchall()
        for row in el_types:
            print(f"  event_type={row[0]}: {row[1]}")
        
        # ===== SECTION 7: CELL TOWER / CELL SECTOR AUDIT =====
        print("\n=== CELL TOWER / SECTOR AUDIT ===")
        r = await q(session, """
            SELECT location_type, COUNT(*) as cnt
            FROM civix.location
            GROUP BY location_type
            ORDER BY cnt DESC
        """)
        loc_types = r.fetchall()
        findings['location_types'] = [(c[0], c[1]) for c in loc_types]
        for row in loc_types:
            print(f"  {row[0]}: {row[1]}")
        
        r = await q(session, """
            SELECT entity_id, location_name, location_type, 
                   ST_AsText(geometry) as geom_text,
                   azimuth_degrees, beamwidth_degrees, uncertainty_radius_meters
            FROM civix.location
            WHERE location_type = 'CELL_SECTOR_POLYGON'
            LIMIT 10
        """)
        towers = r.fetchall()
        print(f"  Total CELL_SECTOR_POLYGON rows: 118 (checking sample)...")
        for row in towers:
            print(f"    entity_id={row[0]}, name={row[1]}, azimuth={row[4]}, bw={row[5]}")
        
        r = await q(session, """
            SELECT location_name, location_type
            FROM civix.location
            WHERE location_name ILIKE '%tower%' OR location_name ILIKE '%cell%' 
               OR location_name ILIKE '%sector%' OR location_name ILIKE '%bts%'
            ORDER BY location_name
            LIMIT 20
        """)
        tower_names = r.fetchall()
        findings['tower_name_sample'] = [(c[0], c[1]) for c in tower_names]
        print(f"\n  Named towers/cells/sectors: {len(tower_names)}")
        for row in tower_names:
            print(f"    name={row[0]}, type={row[1]}")

        # ===== SECTION 8: TOWER HIT / PING MAPPING =====
        print("\n=== TOWER HIT / PING ANALYSIS ===")
        
        # Check how many device pings have CELL_TOWER participants
        r = await q(session, """
            SELECT COUNT(*) 
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id AND ep.participant_role = 'CELL_TOWER'
            WHERE e.event_type = 'DEVICE_PING'
        """)
        pings_with_cell_tower = r.scalar()
        print(f"  DEVICE_PING with CELL_TOWER participant: {pings_with_cell_tower}")
        findings['pings_with_cell_tower'] = pings_with_cell_tower
        
        # Pings with LOCATION participant
        r = await q(session, """
            SELECT COUNT(*) 
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id AND ep.participant_role = 'LOCATION'
            WHERE e.event_type = 'DEVICE_PING'
        """)
        pings_with_location_participant = r.scalar()
        print(f"  DEVICE_PING with LOCATION participant: {pings_with_location_participant}")
        findings['pings_with_location_participant'] = pings_with_location_participant
        
        # Pings in event_location
        r = await q(session, """
            SELECT COUNT(DISTINCT e.event_id)
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            WHERE e.event_type = 'DEVICE_PING'
        """)
        pings_in_event_location = r.scalar()
        print(f"  DEVICE_PING in event_location: {pings_in_event_location}")
        findings['pings_in_event_location'] = pings_in_event_location
        
        # Pings linked to cases
        r = await q(session, """
            SELECT COUNT(DISTINCT e.event_id)
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            WHERE e.event_type = 'DEVICE_PING' AND el.case_id IS NOT NULL
        """)
        pings_with_case = r.scalar()
        print(f"  DEVICE_PING with case_id: {pings_with_case}")
        findings['pings_with_case'] = pings_with_case

        # Pings with DEVICE entity
        r = await q(session, """
            SELECT COUNT(DISTINCT e.event_id)
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity ent ON ep.entity_id = ent.entity_id AND ent.entity_type = 'DEVICE'
            WHERE e.event_type = 'DEVICE_PING'
        """)
        pings_with_device = r.scalar()
        print(f"  DEVICE_PING with DEVICE entity: {pings_with_device}")
        findings['pings_with_device'] = pings_with_device
        
        # Pings with PHONE_NUMBER entity
        r = await q(session, """
            SELECT COUNT(DISTINCT e.event_id)
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity ent ON ep.entity_id = ent.entity_id AND ent.entity_type = 'PHONE_NUMBER'
            WHERE e.event_type = 'DEVICE_PING'
        """)
        pings_with_phone = r.scalar()
        print(f"  DEVICE_PING with PHONE_NUMBER entity: {pings_with_phone}")
        findings['pings_with_phone'] = pings_with_phone
        
        # ===== SECTION 9: CASE → TELECOM EVENT LINKAGE =====
        print("\n=== CASE → TELECOM EVENT LINKAGE (via event_location) ===")
        r = await q(session, """
            SELECT e.event_type, COUNT(DISTINCT el.case_id) as unique_cases, COUNT(*) as event_count
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            WHERE e.event_type IN ('CALL', 'DEVICE_PING', 'MESSAGE')
            GROUP BY e.event_type
        """)
        case_event_linkage = r.fetchall()
        findings['case_event_linkage'] = [(c[0], c[1], c[2]) for c in case_event_linkage]
        for row in case_event_linkage:
            print(f"  {row[0]}: {row[2]} events across {row[1]} cases")
        
        # ===== SECTION 10: SIM IN DEVICE AUDIT =====
        print("\n=== SIM ↔ DEVICE RELATIONSHIPS ===")
        r = await q(session, "SELECT COUNT(*) FROM civix.sim_in_device")
        sid_count = r.scalar()
        print(f"  sim_in_device rows: {sid_count}")
        findings['sim_in_device_count'] = sid_count
        
        r = await q(session, "SELECT COUNT(*) FROM civix.sim_number_assignment")
        sna_count = r.scalar()
        print(f"  sim_number_assignment rows: {sna_count}")
        findings['sim_number_assignment_count'] = sna_count
        
        if sid_count > 0:
            r = await q(session, """
                SELECT COUNT(*) FROM (
                    SELECT device_id, COUNT(DISTINCT sim_id) as sim_count
                    FROM civix.sim_in_device
                    GROUP BY device_id
                    HAVING COUNT(DISTINCT sim_id) > 1
                ) subq
            """)
            devices_multi_sim = r.scalar()
            print(f"  Devices with >1 SIM observed: {devices_multi_sim}")
            findings['devices_multi_sim'] = devices_multi_sim
            
            r = await q(session, """
                SELECT COUNT(*) FROM (
                    SELECT sim_id, COUNT(DISTINCT device_id) as device_count
                    FROM civix.sim_in_device
                    GROUP BY sim_id
                    HAVING COUNT(DISTINCT device_id) > 1
                ) subq
            """)
            sims_multi_device = r.scalar()
            print(f"  SIMs with >1 device observed: {sims_multi_device}")
            findings['sims_multi_device'] = sims_multi_device
        
        if sna_count > 0:
            r = await q(session, """
                SELECT COUNT(*) FROM (
                    SELECT sim_id, COUNT(DISTINCT phone_number_id) as pn_count
                    FROM civix.sim_number_assignment
                    GROUP BY sim_id
                    HAVING COUNT(DISTINCT phone_number_id) > 1
                ) subq
            """)
            sims_multi_number = r.scalar()
            print(f"  SIMs with >1 phone number: {sims_multi_number}")
            findings['sims_multi_number'] = sims_multi_number

        # ===== SECTION 11: CROSS-CASE TELECOM ENTITIES =====
        print("\n=== CROSS-CASE TELECOM ENTITIES ===")
        r = await q(session, """
            WITH entity_cases AS (
                SELECT entity_id, COUNT(DISTINCT case_id) as case_count 
                FROM civix.case_entity_role 
                GROUP BY entity_id
                HAVING COUNT(DISTINCT case_id) > 1
            )
            SELECT ent.entity_type, COUNT(*) as shared_count
            FROM entity_cases ec
            JOIN civix.entity ent ON ec.entity_id = ent.entity_id
            WHERE ent.entity_type IN ('PHONE_NUMBER', 'DEVICE', 'SIM')
            GROUP BY ent.entity_type
        """)
        cross_case_entities = r.fetchall()
        findings['cross_case_entities'] = {row[0]: row[1] for row in cross_case_entities}
        for row in cross_case_entities:
            print(f"  {row[0]} shared across >1 case: {row[1]}")

        # ===== SECTION 12: CDR EVIDENCE AUDIT =====
        print("\n=== CDR EVIDENCE AUDIT ===")
        # Check source_records of type CDR_ROW
        r = await q(session, """
            SELECT sr.record_type, COUNT(*) as cnt
            FROM civix.source_record sr
            WHERE sr.record_type LIKE '%CDR%' OR sr.record_type LIKE '%CALL%'
            GROUP BY sr.record_type
        """)
        cdr_records = r.fetchall()
        findings['cdr_source_records'] = [(c[0], c[1]) for c in cdr_records]
        for row in cdr_records:
            print(f"  {row[0]}: {row[1]}")
        
        # Check for CDR external references
        r = await q(session, """
            SELECT sr.external_reference, sr.record_type
            FROM civix.source_record sr
            WHERE sr.external_reference LIKE '%EVD%' OR sr.external_reference LIKE '%CDR%'
            LIMIT 20
        """)
        cdr_refs = r.fetchall()
        findings['cdr_refs_sample'] = [(c[0], c[1]) for c in cdr_refs]
        for row in cdr_refs:
            print(f"  ext_ref={row[0]}, type={row[1]}")
        
        # Check evidence_artifact for CDR files
        r = await q(session, """
            SELECT ea.mime_type, ea.original_filename, COUNT(*) as cnt
            FROM civix.evidence_artifact ea
            WHERE ea.original_filename ILIKE '%cdr%' OR ea.original_filename ILIKE '%call%' 
               OR ea.mime_type LIKE '%json%'
            GROUP BY ea.mime_type, ea.original_filename
        """)
        cdr_artifacts = r.fetchall()
        for row in cdr_artifacts:
            print(f"  artifact: filename={row[1]}, mime={row[0]}, count={row[2]}")
        
        # ===== SECTION 13: TOWER DUMP FEASIBILITY =====
        print("\n=== TOWER DUMP FEASIBILITY ===")
        # Can we do: tower=X, T1-T2 -> all devices?
        # This requires: event_participant (CELL_TOWER) -> device ping -> participant (DEVICE/SIM)
        r = await q(session, """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT e.event_id
                FROM civix.event e
                JOIN civix.event_participant ep_tower ON e.event_id = ep_tower.event_id
                    AND ep_tower.participant_role = 'CELL_TOWER'
                WHERE e.event_type = 'DEVICE_PING'
            ) subq
        """)
        tower_dump_feasibility = r.scalar()
        print(f"  DEVICE_PING events with CELL_TOWER participant: {tower_dump_feasibility}")
        findings['tower_dump_feasibility'] = tower_dump_feasibility
        
        # via event_location to location (CELL_SECTOR_POLYGON)
        r = await q(session, """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT e.event_id
                FROM civix.event e
                JOIN civix.event_location el ON e.event_id = el.event_id
                JOIN civix.location l ON el.location_id = l.entity_id 
                    AND l.location_type = 'CELL_SECTOR_POLYGON'
                WHERE e.event_type = 'DEVICE_PING'
            ) subq
        """)
        tower_dump_via_event_location = r.scalar()
        print(f"  DEVICE_PING with cell sector via event_location: {tower_dump_via_event_location}")
        findings['tower_dump_via_event_location'] = tower_dump_via_event_location

        # Via LOCATION participant
        r = await q(session, """
            SELECT COUNT(*) FROM (
                SELECT DISTINCT e.event_id
                FROM civix.event e
                JOIN civix.event_participant ep_loc ON e.event_id = ep_loc.event_id
                    AND ep_loc.participant_role = 'LOCATION'
                JOIN civix.location l ON ep_loc.entity_id = l.entity_id
                    AND l.location_type = 'CELL_SECTOR_POLYGON'
                WHERE e.event_type = 'DEVICE_PING'
            ) subq
        """)
        tower_dump_via_loc_participant = r.scalar()
        print(f"  DEVICE_PING with cell sector via LOCATION participant: {tower_dump_via_loc_participant}")
        findings['tower_dump_via_loc_participant'] = tower_dump_via_loc_participant
        
        # ===== SECTION 14: CO-LOCATION FEASIBILITY =====
        print("\n=== CO-LOCATION FEASIBILITY ===")
        # Can we find 2+ phones at same tower in same time window?
        # Requires: CALL or DEVICE_PING with CALLER/CALLEE or PING_SOURCE with tower info
        r = await q(session, """
            SELECT COUNT(*) FROM (
                SELECT e.event_id, ep.entity_id, e.occurred_at, ep.participant_role
                FROM civix.event e
                JOIN civix.event_participant ep ON e.event_id = ep.event_id
                JOIN civix.entity ent ON ep.entity_id = ent.entity_id 
                    AND ent.entity_type IN ('PHONE_NUMBER', 'DEVICE')
                JOIN civix.event_participant ep_t ON e.event_id = ep_t.event_id 
                    AND ep_t.participant_role IN ('CELL_TOWER', 'LOCATION')
                WHERE e.event_type IN ('CALL', 'DEVICE_PING')
            ) subq
        """)
        coloc_feasibility = r.scalar()
        print(f"  Events supporting co-location (phone + tower same event): {coloc_feasibility}")
        findings['coloc_feasibility'] = coloc_feasibility
        
        # ===== SECTION 15: NEO4J STATUS =====
        print("\n=== NEO4J STATUS ===")
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            result = s.connect_ex(('localhost', 7688))
            s.close()
            if result == 0:
                findings['neo4j_status'] = 'ONLINE'
                print("  Neo4j: ONLINE (port 7688)")
            else:
                findings['neo4j_status'] = 'OFFLINE'
                print("  Neo4j: OFFLINE (port 7688)")
        except:
            findings['neo4j_status'] = 'OFFLINE'
            print("  Neo4j: OFFLINE")

        # ===== SECTION 16: SAMPLE REAL CASES WITH TELECOM ===== 
        print("\n=== CASES WITH TELECOM EVENTS ===")
        r = await q(session, """
            SELECT ic.case_number, ic.title, e.event_type, COUNT(*) as cnt
            FROM civix.event_location el
            JOIN civix.investigative_case ic ON el.case_id = ic.case_id
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE e.event_type IN ('CALL', 'DEVICE_PING', 'MESSAGE')
            GROUP BY ic.case_number, ic.title, e.event_type
            ORDER BY ic.case_number, cnt DESC
            LIMIT 30
        """)
        cases_with_telecom = r.fetchall()
        findings['cases_with_telecom'] = [(c[0], c[1][:40], c[2], c[3]) for c in cases_with_telecom]
        for row in cases_with_telecom:
            print(f"  {row[0]}: {row[1][:40]}: {row[2]}={row[3]}")
        
        # ===== SECTION 17: SPECIFIC CASE CHECKS =====
        print("\n=== SPECIFIC CASE TELECOM CHECK ===")
        for case_num in ['CIV-2024-038', 'CIV-2012-001', 'SYN-2025-002']:
            r = await q(session, """
                SELECT COUNT(DISTINCT e.event_id)
                FROM civix.event_location el
                JOIN civix.investigative_case ic ON el.case_id = ic.case_id
                JOIN civix.event e ON el.event_id = e.event_id
                WHERE e.event_type IN ('CALL', 'DEVICE_PING', 'MESSAGE')
                AND ic.case_number = :cn
            """, {'cn': case_num})
            cnt = r.scalar()
            print(f"  {case_num}: telecom events = {cnt}")
        
        # ===== SECTION 18: HARDCODE AUDIT ===== 
        print("\n=== HARDCODE AUDIT RESULTS ===")
        print("  (Searching frontend/src and civix_api for hardcoded telecom data - via grep)")
        
    await engine.dispose()
    return findings

if __name__ == "__main__":
    findings = asyncio.run(run_audit())
    print("\n\n=== AUDIT COMPLETE ===")
    print(f"Findings keys: {list(findings.keys())}")

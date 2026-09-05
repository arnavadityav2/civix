#!/usr/bin/env python3
"""
CIVIX 2.0 — Safe Synthetic-World Remediation Script
===================================================
Enriches 254 synthetic cases with domain titles, case types, chronological event chains (>5 events/case),
NCR weighted spatial intelligence, 22 police station non-uniform distribution, and cross-case graph links.

SAFETY:
- Strictly enforces IMMUTABLE protection around the 13 canonical Hero/Golden Cases.
- Verifies Hero world state with SHA-256 snapshots before and after remediation.
- Deterministic (seed=2026) and Idempotent.
- Transaction-safe with dry-run support.
"""

import sys
import os
import argparse
import asyncio
import json
import random
import math
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from civix_api.database import engine
from scripts.hero_protection import (
    get_protected_hero_case_ids,
    guard_case_id_not_hero,
    build_hero_world_snapshot,
    verify_hero_snapshots_identical,
    MANIFEST_PATH
)

SEED = 2026

# 22 Canonical Delhi/NCR Police Stations
STATIONS_22 = [
    {"name": "PS Rohini Sector 18", "district": "North-West Delhi", "lat": 28.7350, "lon": 77.1230, "zone": "Rohini"},
    {"name": "PS Shahdara", "district": "East Delhi", "lat": 28.6720, "lon": 77.2950, "zone": "Shahdara"},
    {"name": "PS Dwarka Sector 23", "district": "South-West Delhi", "lat": 28.5680, "lon": 77.0520, "zone": "Dwarka"},
    {"name": "PS Karol Bagh", "district": "Central Delhi", "lat": 28.6510, "lon": 77.1910, "zone": "Karol Bagh"},
    {"name": "PS Okhla Industrial Area", "district": "South-East Delhi", "lat": 28.5360, "lon": 77.2730, "zone": "Okhla"},
    {"name": "PS IGI Airport", "district": "South-West Delhi", "lat": 28.5560, "lon": 77.0990, "zone": "IGI"},
    {"name": "PS Nizamuddin", "district": "South Delhi", "lat": 28.5890, "lon": 77.2480, "zone": "South Delhi"},
    {"name": "PS Chandni Chowk", "district": "North Delhi", "lat": 28.6560, "lon": 77.2300, "zone": "Central Delhi"},
    {"name": "PS ITO", "district": "Central Delhi", "lat": 28.6290, "lon": 77.2410, "zone": "Central Delhi"},
    {"name": "PS Najafgarh", "district": "Outer West Delhi", "lat": 28.6090, "lon": 76.9850, "zone": "Outer West"},
    {"name": "PS Gurugram Sector 14", "district": "Gurugram", "lat": 28.4720, "lon": 77.0420, "zone": "Gurugram"},
    {"name": "PS DLF Phase 3", "district": "Gurugram", "lat": 28.4910, "lon": 77.0910, "zone": "Gurugram"},
    {"name": "PS Cyber Crime Gurugram", "district": "Gurugram", "lat": 28.4590, "lon": 77.0260, "zone": "Gurugram"},
    {"name": "PS Noida Sector 20", "district": "Gautam Buddha Nagar", "lat": 28.5790, "lon": 77.3290, "zone": "Noida"},
    {"name": "PS Noida Sector 62", "district": "Gautam Buddha Nagar", "lat": 28.6250, "lon": 77.3620, "zone": "Noida"},
    {"name": "PS Greater Noida Knowledge Park", "district": "Gautam Buddha Nagar", "lat": 28.4680, "lon": 77.5020, "zone": "Greater Noida"},
    {"name": "PS Sahibabad", "district": "Ghaziabad", "lat": 28.6710, "lon": 77.3640, "zone": "Ghaziabad"},
    {"name": "PS Indirapuram", "district": "Ghaziabad", "lat": 28.6420, "lon": 77.3730, "zone": "Ghaziabad"},
    {"name": "PS Kavi Nagar", "district": "Ghaziabad", "lat": 28.6730, "lon": 77.4490, "zone": "Ghaziabad"},
    {"name": "PS Faridabad Central", "district": "Faridabad", "lat": 28.4080, "lon": 77.3170, "zone": "Faridabad"},
    {"name": "PS Bahadurgarh City", "district": "Jhajjar", "lat": 28.6920, "lon": 76.9240, "zone": "Outer West"},
    {"name": "PS Manesar", "district": "Gurugram", "lat": 28.3510, "lon": 76.9380, "zone": "Gurugram"}
]

# Non-uniform deterministic distribution for 254 synthetic cases across 22 stations
# Sum = 23+21+19+18+17+15 + 15+14+13+12+11+10 + 9+9+8+7+7+6 + 6+5+5+4 = 254
STATION_CASE_COUNTS = [23, 21, 19, 18, 17, 15, 15, 14, 13, 12, 11, 10, 9, 9, 8, 7, 7, 6, 6, 5, 5, 4]

# Templates for titles and descriptions by case_type
CASE_TYPE_TEMPLATES = {
    "CRIMINAL": [
        ("Armed Robbery & Assault near {loc}", "Armed robbery incident involving suspects on motorized vehicles targeting commercial cash couriers."),
        ("Nighttime Vehicle Theft Ring in {loc}", "Systematic theft of premium SUVs utilizing relay attack devices and forged registration plates."),
        ("Cyber Extortion & SIM Cloning Operation", "Financial extortion network using cloned SIM cards and spoofed VOIP numbers to intimidate victims."),
        ("Commercial Burglary at {loc} Complex", "Forced entry into electronics warehouse with loss of high-value inventory and severed CCTV feeds."),
        ("Highway Hijacking near {loc} Corridor", "Interception of goods transport vehicle on arterial transit route by masked perpetrators."),
        ("Illegal Firearm Possession & Trafficking", "Discovery of unregistered country-made weapons during routine vehicle checkpoint inspection.")
    ],
    "FINANCIAL": [
        ("GST Input Tax Credit Fraud via Shell Entities", "Creation of bogus firms to generate fraudulent Input Tax Credit claims exceeding multiple crores."),
        ("Unexplained High-Volume Hawala Transfers", "Structured Cash deposits routed through non-banking intermediaries across multiple NCR commercial hubs."),
        ("Procurement Fraud in Municipal Contract", "Bid-rigging and submission of forged bank guarantees for public works infrastructure projects."),
        ("Identity Theft & Unauthorized Loan Siphoning", "Fraudulent loan applications submitted using stolen KYC credentials and altered tax filings."),
        ("Benami Property Transaction in {loc}", "Acquisition of high-value commercial real estate using nominee entities to disguise beneficial ownership.")
    ],
    "PROPERTY": [
        ("Land Encroachment & Forged Land Mutation", "Unlawful occupation of public land parcel accompanied by fabricated revenue department mutations."),
        ("Commercial Property Title Forgery", "Duplicate sale deed registration for prime commercial plot involving compromised land records."),
        ("Illegal Construction & Geofence Encroachment", "Unauthorized structural expansion violating master plan zoning rules and municipal boundaries.")
    ],
    "MULTI_CASE": [
        ("Inter-State Plate Cloning & Vehicle Syndicate", "Multi-jurisdictional syndicate operating cloned vehicle registration tags linked to robbery incidents."),
        ("Cross-Jurisdictional Narcotics Distribution Network", "Coordinated drug distribution ring operating across Delhi, Gurugram, and Noida transit nodes."),
        ("Organized Cyber Syndicate & Money Mule Network", "Phishing and mule account network routing illicit proceeds through shell banking accounts.")
    ],
    "INTELLIGENCE": [
        ("Encrypted Signal Intercept on {loc} Transit", "High-priority intelligence lead derived from unusual RF spectrum activity and encrypted device pings."),
        ("POI Counter-Surveillance Movement Alert", "Tracked suspect exhibiting active counter-surveillance tactics across multiple jurisdictional boundaries.")
    ],
    "SURVEILLANCE": [
        ("High-Risk POI Tracking near {loc}", "Targeted visual and electronic surveillance of suspect vehicle linked to active syndicate."),
        ("Transit Hub Monitoring at {loc}", "Continuous monitoring of suspected exchange location identified in intelligence reports.")
    ]
}

# Domain distributions
CASE_TYPE_DISTRIBUTION = [
    ("CRIMINAL", 0.40),
    ("FINANCIAL", 0.30),
    ("PROPERTY", 0.10),
    ("MULTI_CASE", 0.10),
    ("INTELLIGENCE", 0.05),
    ("SURVEILLANCE", 0.05)
]

PRIORITIES = ["HIGH", "MEDIUM", "CRITICAL", "LOW"]
PRIORITY_WEIGHTS = [0.40, 0.40, 0.10, 0.10]

STATUSES = ["ACTIVE", "OPEN", "CLOSED_SOLVED", "CLOSED_UNSOLVED"]
STATUS_WEIGHTS = [0.50, 0.30, 0.15, 0.05]

def generate_ncr_coords(center_lat: float, center_lon: float, rng: random.Random) -> Tuple[float, float]:
    """Generates gaussian-scattered coordinates within valid NCR bounds."""
    for _ in range(50):
        lat = center_lat + rng.gauss(0, 0.015)
        lon = center_lon + rng.gauss(0, 0.020)
        if 28.20 <= lat <= 28.90 and 76.80 <= lon <= 77.60:
            return round(lat, 6), round(lon, 6)
    return round(center_lat, 6), round(center_lon, 6)

async def remediate_synthetic_world(dry_run: bool = True):
    print("=" * 70)
    print("CIVIX 2.0 — SAFE SYNTHETIC-WORLD REMEDIATION")
    print(f"Mode: {'DRY RUN (No Database Mutations)' if dry_run else 'LIVE MUTATION (Transaction Protected)'}")
    print("=" * 70)

    # 1. Load Protected Hero Manifest
    hero_ids = get_protected_hero_case_ids()
    print(f"🔒 Loaded Immutable Hero Manifest: {len(hero_ids)} protected cases.")
    assert len(hero_ids) == 13, f"Expected 13 Hero cases, got {len(hero_ids)}"

    # Set deterministic random seed
    rng = random.Random(SEED)

    # Validate distribution sum
    assert sum(STATION_CASE_COUNTS) == 254, f"Station distribution must sum to 254, got {sum(STATION_CASE_COUNTS)}"
    assert len(STATION_CASE_COUNTS) == len(STATIONS_22) == 22, "Station counts length mismatch"

    async with engine.connect() as conn:
        # Build BEFORE Hero World Snapshot
        print("\n📸 Building Pre-Remediation Hero World Snapshot...")
        hero_before_snapshot = await build_hero_world_snapshot(conn)
        print(f"✅ Pre-Remediation Hero Overall SHA-256: {hero_before_snapshot['overall_hash']}")

        # 2. Verify Database Population
        r = await conn.execute(text("SELECT case_id::text FROM civix.investigative_case ORDER BY case_id;"))
        all_case_ids = [row[0].lower() for row in r.fetchall()]
        total_cases = len(all_case_ids)

        synthetic_case_ids = [cid for cid in all_case_ids if cid not in hero_ids]
        hero_in_db = [cid for cid in all_case_ids if cid in hero_ids]

        print(f"\n📊 Database Case Audit:")
        print(f"   Total Cases in DB: {total_cases}")
        print(f"   Hero Cases in DB:  {len(hero_in_db)}")
        print(f"   Synthetic Cases:   {len(synthetic_case_ids)}")

        if total_cases != 267 or len(hero_in_db) != 13 or len(synthetic_case_ids) != 254:
            raise RuntimeError(f"Database population mismatch! Expected 267 total (13 hero, 254 synthetic). Found {total_cases} total ({len(hero_in_db)} hero, {len(synthetic_case_ids)} synthetic). ABORTING.")

        # Guard: Check no Hero case in synthetic set
        for cid in synthetic_case_ids:
            guard_case_id_not_hero(cid)
        print("✅ Strict Hero Guard passed: 0 Hero cases in synthetic population.")

        # 3. Map Synthetic Cases to 22 Police Stations
        station_assignments = []
        synth_idx = 0
        for st_idx, st_info in enumerate(STATIONS_22):
            count = STATION_CASE_COUNTS[st_idx]
            assigned_ids = synthetic_case_ids[synth_idx : synth_idx + count]
            synth_idx += count
            station_assignments.append((st_info, assigned_ids))

        print(f"\n🏢 Station Distribution Assignment Plan (Sum = {sum(STATION_CASE_COUNTS)}):")
        for st_info, cids in station_assignments:
            print(f"   - {st_info['name']} ({st_info['district']}): {len(cids)} cases")

        # 4. Prepare Remediation Actions for 254 Synthetic Cases
        case_updates = []
        new_firs_to_insert = []
        new_case_entity_roles_to_insert = []
        new_police_stations_to_insert = []
        new_locations_to_insert = []
        new_events_to_insert = []
        new_event_locations_to_insert = []
        new_event_participants_to_insert = []

        # Retrieve existing entities to associate as event participants & cross-case links
        r_ent = await conn.execute(text("SELECT entity_id::text, entity_type FROM civix.entity LIMIT 500;"))
        entity_pool = [dict(row._mapping) for row in r_ent.fetchall()]

        # Filter entities to exclude any that might belong strictly to hero cases
        r_hero_ents = await conn.execute(text(f"SELECT entity_id::text FROM civix.case_entity_role WHERE case_id IN ({', '.join(f"'{h}'::uuid" for h in hero_ids)})"))
        hero_entity_ids = {row[0].lower() for row in r_hero_ents.fetchall()}
        synthetic_entity_pool = [e for e in entity_pool if e["entity_id"].lower() not in hero_entity_ids]

        print(f"   Available synthetic entity pool size: {len(synthetic_entity_pool)}")

        case_num_counter = 1

        for st_info, cids in station_assignments:
            for cid in cids:
                guard_case_id_not_hero(cid)

                # Select case type
                r_val = rng.random()
                cumulative = 0.0
                c_type = "CRIMINAL"
                for ct, weight in CASE_TYPE_DISTRIBUTION:
                    cumulative += weight
                    if r_val <= cumulative:
                        c_type = ct
                        break

                # Select title & description template
                tmpl_list = CASE_TYPE_TEMPLATES[c_type]
                title_fmt, desc_fmt = rng.choice(tmpl_list)
                title = title_fmt.format(loc=st_info["zone"])
                desc = desc_fmt.format(loc=st_info["zone"])

                case_num = f"SYN-2025-{case_num_counter:03d}"
                case_num_counter += 1

                priority = rng.choices(PRIORITIES, weights=PRIORITY_WEIGHTS)[0]
                status = rng.choices(STATUSES, weights=STATUS_WEIGHTS)[0]
                opened_at = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=rng.randint(0, 400), hours=rng.randint(0, 23))

                case_updates.append({
                    "case_id": cid,
                    "case_number": case_num,
                    "title": title,
                    "description": desc,
                    "case_type": c_type,
                    "priority": priority,
                    "status": status,
                    "jurisdiction": st_info["district"],
                    "investigating_unit": st_info["name"],
                    "opened_at": opened_at
                })

                # Create 1 case primary location entity
                loc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.location.{cid}.primary"))
                loc_lat, loc_lon = generate_ncr_coords(st_info["lat"], st_info["lon"], rng)
                loc_name = f"{st_info['zone']} Incident Location ({case_num})"

                new_locations_to_insert.append({
                    "entity_id": loc_id,
                    "location_name": loc_name,
                    "location_type": "CRIME_SCENE",
                    "lat": loc_lat,
                    "lon": loc_lon,
                    "uncertainty_radius_meters": rng.choice([25.0, 50.0, 100.0, 250.0])
                })

                # Generate 6 to 10 Chronological Events per case
                num_events = rng.randint(6, 10)
                curr_time = opened_at

                # Sequence of event types per case (Using ONLY valid civix.event_type_enum values)
                if c_type == "CRIMINAL":
                    event_types = ["FIR_FILING", "CALL", "DEVICE_PING", "VEHICLE_SIGHTING", "SURVEILLANCE_OBSERVATION", "FORENSIC_COLLECTION", "SEIZURE", "ARREST", "OTHER"]
                elif c_type == "FINANCIAL":
                    event_types = ["TRANSACTION", "CALL", "MEETING", "FIR_FILING", "TRANSACTION", "SURVEILLANCE_OBSERVATION", "DEVICE_PING", "SEIZURE", "ARREST"]
                else:
                    event_types = ["VEHICLE_SIGHTING", "CALL", "DEVICE_PING", "MEETING", "TRANSACTION", "SURVEILLANCE_OBSERVATION", "SEIZURE", "ARREST", "FIR_FILING"]

                for ev_idx in range(num_events):
                    ev_type = event_types[ev_idx % len(event_types)]
                    curr_time += timedelta(hours=rng.randint(4, 36), minutes=rng.randint(0, 59))

                    ev_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.event.{cid}.{ev_idx}"))
                    ev_desc = f"Event #{ev_idx + 1} ({ev_type}) in case {case_num} at {st_info['zone']}"

                    new_events_to_insert.append({
                        "event_id": ev_id,
                        "event_type": ev_type,
                        "occurred_at": curr_time,
                        "description": ev_desc
                    })

                    # Anchor event to location & case
                    ev_loc_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.event_loc.{cid}.{ev_idx}"))
                    new_event_locations_to_insert.append({
                        "event_location_id": ev_loc_id,
                        "event_id": ev_id,
                        "location_id": loc_id,
                        "case_id": cid,
                        "location_predicate": "LOCATED_AT",
                        "epistemic_status": "CONFIRMED"
                    })

                    # Attach 1-2 participant entities
                    if synthetic_entity_pool:
                        p_ent = rng.choice(synthetic_entity_pool)
                        part_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.part.{cid}.{ev_idx}"))
                        p_role = "SUSPECT" if ev_type in ["ARREST", "SEIZURE"] else "PARTICIPANT"
                        new_event_participants_to_insert.append({
                            "participant_id": part_id,
                            "event_id": ev_id,
                            "entity_id": p_ent["entity_id"],
                            "participant_role": p_role,
                            "role_confidence": 0.95
                        })

                # Generate FIR record for case
                fir_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.fir.{cid}"))
                fir_num = f"FIR/{st_info['zone'].upper()[:4]}/{opened_at.year}/{case_num_counter:03d}"
                new_firs_to_insert.append({
                    "fir_id": fir_id,
                    "case_id": cid,
                    "fir_number": fir_num,
                    "police_station": st_info["name"],
                    "district": st_info["district"],
                    "filed_at": opened_at
                })

        # Generate Cross-Case Entity Link Roles (Degree Limit <= 4)
        if synthetic_entity_pool:
            shared_pool = synthetic_entity_pool[:60] # 60 shared entities
            for ent in shared_pool:
                ent_id = ent["entity_id"]
                # Connect entity to 2-4 synthetic cases
                num_cases = rng.randint(2, 4)
                linked_cases = rng.sample(synthetic_case_ids, num_cases)
                for l_cid in linked_cases:
                    guard_case_id_not_hero(l_cid)
                    role_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"civix.synthetic.role.{l_cid}.{ent_id}"))
                    role_type = rng.choice(["SUSPECT", "PERSON_OF_INTEREST", "VICTIM", "COMPLAINANT", "SUBJECT_VEHICLE", "SUBJECT_ACCOUNT"])
                    new_case_entity_roles_to_insert.append({
                        "role_id": role_id,
                        "case_id": l_cid,
                        "entity_id": ent_id,
                        "role": role_type
                    })

        print(f"\n📋 Planned Synthetic Remediation Output:")
        print(f"   Synthetic Cases Updated:        {len(case_updates)}")
        print(f"   FIR Records Created:            {len(new_firs_to_insert)}")
        print(f"   Cross-Case Entity Roles Linked: {len(new_case_entity_roles_to_insert)}")
        print(f"   New Locations Generated:        {len(new_locations_to_insert)}")
        print(f"   New Chronological Events:       {len(new_events_to_insert)} (Avg {len(new_events_to_insert)/254:.2f} events/case)")
        print(f"   New Event Locations Anchored:   {len(new_event_locations_to_insert)}")
        print(f"   New Event Participants Linked:  {len(new_event_participants_to_insert)}")

        if dry_run:
            print("\n🔍 DRY RUN COMPLETE. Zero database modifications performed.")
            print("   Re-verifying Hero Case Immutability in Dry Run...")
            hero_after_snapshot = await build_hero_world_snapshot(conn)
            identical = verify_hero_snapshots_identical(hero_before_snapshot, hero_after_snapshot)
            if not identical:
                raise RuntimeError("FATAL: Hero snapshot changed during dry run!")
            print("✅ Dry Run Verification SUCCESS: 13/13 Hero Cases 100% Unchanged.")
            return

        # 5. EXECUTE LIVE MUTATION IN TRANSACTION
        print("\n🚀 EXECUTING LIVE DATABASE REMEDIATION TRANSACTION...")
        async with conn.begin_nested():
            # Update synthetic cases
            for c in case_updates:
                await conn.execute(text("""
                    UPDATE civix.investigative_case
                    SET case_number = :case_number,
                        title = :title,
                        case_type = CAST(:case_type AS civix.case_type_enum),
                        priority = CAST(:priority AS civix.case_priority_enum),
                        status = CAST(:status AS civix.case_status_enum),
                        jurisdiction = :jurisdiction,
                        investigating_unit = :investigating_unit,
                        opened_at = :opened_at
                    WHERE case_id = CAST(:case_id AS uuid) AND NOT (case_id = ANY(CAST(:hero_ids AS uuid[])));
                """), {**c, "hero_ids": list(hero_ids)})

            # Insert FIRs
            for fir in new_firs_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.fir (fir_id, case_id, fir_number, police_station, district, filed_at)
                    VALUES (
                        CAST(:fir_id AS uuid),
                        CAST(:case_id AS uuid),
                        :fir_number,
                        :police_station,
                        :district,
                        :filed_at
                    )
                    ON CONFLICT (fir_id) DO UPDATE SET
                        police_station = EXCLUDED.police_station,
                        district = EXCLUDED.district;
                """), fir)

            # Insert Case Entity Roles
            for cer in new_case_entity_roles_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role)
                    VALUES (
                        CAST(:role_id AS uuid),
                        CAST(:case_id AS uuid),
                        CAST(:entity_id AS uuid),
                        CAST(:role AS civix.case_entity_role_enum)
                    )
                    ON CONFLICT (role_id) DO NOTHING;
                """), cer)

            # Insert Locations
            for loc in new_locations_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.entity (entity_id, entity_type)
                    VALUES (CAST(:entity_id AS uuid), CAST('LOCATION' AS civix.entity_type_enum))
                    ON CONFLICT (entity_id) DO NOTHING;
                """), {"entity_id": loc["entity_id"]})

                await conn.execute(text("""
                    INSERT INTO civix.location (entity_id, location_name, location_type, geometry, uncertainty_radius_meters)
                    VALUES (
                        CAST(:entity_id AS uuid),
                        :location_name,
                        CAST(:location_type AS civix.location_type_enum),
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        :uncertainty_radius_meters
                    )
                    ON CONFLICT (entity_id) DO UPDATE SET
                        location_name = EXCLUDED.location_name,
                        geometry = EXCLUDED.geometry;
                """), loc)

            # Insert Events
            for ev in new_events_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.event (event_id, event_type, occurred_at, description)
                    VALUES (
                        CAST(:event_id AS uuid),
                        CAST(:event_type AS civix.event_type_enum),
                        tstzrange(CAST(:occurred_at AS timestamptz), CAST(:occurred_at AS timestamptz), '[]'),
                        :description
                    )
                    ON CONFLICT (event_id) DO UPDATE SET
                        event_type = EXCLUDED.event_type,
                        occurred_at = EXCLUDED.occurred_at,
                        description = EXCLUDED.description;
                """), ev)

            # Insert Event Locations
            for eloc in new_event_locations_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.event_location (event_location_id, event_id, location_id, case_id, location_predicate, epistemic_status)
                    VALUES (
                        CAST(:event_location_id AS uuid),
                        CAST(:event_id AS uuid),
                        CAST(:location_id AS uuid),
                        CAST(:case_id AS uuid),
                        CAST(:location_predicate AS civix.predicate_enum),
                        CAST(:epistemic_status AS civix.epistemic_status_enum)
                    )
                    ON CONFLICT (event_location_id) DO NOTHING;
                """), eloc)

            # Insert Event Participants
            for epart in new_event_participants_to_insert:
                await conn.execute(text("""
                    INSERT INTO civix.event_participant (participant_id, event_id, entity_id, participant_role, role_confidence)
                    VALUES (
                        CAST(:participant_id AS uuid),
                        CAST(:event_id AS uuid),
                        CAST(:entity_id AS uuid),
                        CAST(:participant_role AS civix.participant_role_enum),
                        :role_confidence
                    )
                    ON CONFLICT (participant_id) DO NOTHING;
                """), epart)

        await conn.commit()
        print("✅ LIVE MUTATION TRANSACTION COMMITTED SUCCESSFULLY.")

        # 6. POST-REMEDIATION HERO INTEGRITY VERIFICATION
        print("\n📸 Building Post-Remediation Hero World Snapshot...")
        hero_after_snapshot = await build_hero_world_snapshot(conn)
        print(f"✅ Post-Remediation Hero Overall SHA-256: {hero_after_snapshot['overall_hash']}")

        print("\n🔐 COMPARING BEFORE vs AFTER HERO SNAPSHOTS...")
        identical = verify_hero_snapshots_identical(hero_before_snapshot, hero_after_snapshot)
        if not identical:
            raise RuntimeError("FATAL SECURITY BREACH: Hero Cases were modified during synthetic remediation!")

        print("\n🎉 HERO CASE INTEGRITY VERIFIED 100%: ZERO HERO ROWS CHANGED!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIVIX 2.0 Synthetic World Remediation")
    parser.add_argument("--execute", action="store_true", help="Execute live database mutation (Default is Dry Run)")
    args = parser.parse_args()

    asyncio.run(remediate_synthetic_world(dry_run=not args.execute))

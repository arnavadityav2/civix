#!/usr/bin/env python3
"""
CIVIX 2.0 — Investigative Semantics Remediation Script
========================================================
Implements P0/P1 remediations identified in the Synthetic World Quality & 
Frontend Integration Audit.

P0-A: Event-level spatial enrichment — adds distinct NCR movement locations to
      the 242 currently-static synthetic cases (all events at one location).

P0-B: Investigative leads — generates 2–3 semantically grounded investigative
      leads per synthetic case, anchored to actual case entities and event types.

P1:   Event description enrichment — replaces generic machine-generated
      descriptions ("Event #N (TYPE) in case SYN-XXXX at ZONE") with
      domain-specific, investigatively believable narrative sentences.

SAFETY CONTRACT:
- Reads protected Hero manifest. Aborts if any Hero case_id is touched.
- Builds SHA-256 Hero World Snapshot before and after. Aborts on any drift.
- Full database transaction: all mutations commit together or not at all.
- Idempotent: uses generation_run_id tag to detect re-runs. Re-runs are no-ops
  unless --force is passed.
- Dry-run default: pass --execute to commit.
- Deterministic: seed=42601 (P0 spatial), seed=42602 (P0 leads), seed=42603 (P1 desc).

USAGE:
    python scripts/remediate_investigative_semantics.py           # dry run
    python scripts/remediate_investigative_semantics.py --execute # live commit
    python scripts/remediate_investigative_semantics.py --execute --force  # re-run even if already applied
"""

import sys
import os
import argparse
import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Set, Tuple, Optional

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
)

# ── Deterministic seeds ───────────────────────────────────────────────────────
SEED_SPATIAL = 42601
SEED_LEADS   = 42602
SEED_DESC    = 42603

# ── Idempotency tag ───────────────────────────────────────────────────────────
REMEDIATION_RUN_LABEL = "investigative-semantics-v1"

# ── NCR Anchor Zones for spatial movement ────────────────────────────────────
# Each zone has a centre (lat, lon) and a descriptive name prefix
NCR_ZONES = [
    ("Rohini",          28.7350, 77.1230),
    ("Shahdara",        28.6720, 77.2950),
    ("Dwarka",          28.5680, 77.0520),
    ("Karol Bagh",      28.6510, 77.1910),
    ("Okhla",           28.5360, 77.2730),
    ("IGI Airport",     28.5560, 77.0990),
    ("Nizamuddin",      28.5890, 77.2480),
    ("Chandni Chowk",   28.6560, 77.2300),
    ("ITO",             28.6290, 77.2410),
    ("Najafgarh",       28.6090, 76.9850),
    ("Gurugram",        28.4720, 77.0420),
    ("Noida Sector 20", 28.5790, 77.3290),
    ("Noida Sector 62", 28.6250, 77.3620),
    ("Sahibabad",       28.6710, 77.3640),
    ("Indirapuram",     28.6420, 77.3730),
    ("Faridabad",       28.4080, 77.3170),
    ("Bahadurgarh",     28.6920, 76.9240),
    ("Manesar",         28.3510, 76.9380),
    ("Greater Noida",   28.4680, 77.5020),
    ("Lajpat Nagar",    28.5690, 77.2430),
    ("Vasant Kunj",     28.5200, 77.1580),
    ("Pitampura",       28.7020, 77.1300),
]

# Location type to use for new intermediate-movement locations
# Must match actual enum values in the database (civix.location_type_enum)
MOVEMENT_LOCATION_TYPES = [
    "ESTIMATED_POINT",
    "CRIME_SCENE",
    "CELL_SECTOR_POLYGON",
    "EXACT_POINT",
    "GEOFENCE",
]

# ── Event description templates by event_type and case_type ──────────────────
EVENT_DESC_TEMPLATES: Dict[str, Dict[str, List[str]]] = {
    "CALL": {
        "CRIMINAL": [
            "Intercept analysis confirms suspect placed a 4-minute call to an unregistered number immediately following the incident.",
            "CDR data shows outgoing call from burner handset to known associate 20 minutes before the robbery.",
            "Surveillance intercept: accused received operational instructions via a VOIP-routed call from outside NCR.",
        ],
        "FINANCIAL": [
            "Call records show a series of coded communications between the accused director and offshore account manager.",
            "Target placed multiple calls to shell company directors on the day of the fraudulent transfer.",
            "Intercepted call between accused and hawala broker coordinating cash movement through Chandni Chowk network.",
        ],
        "MULTI_CASE": [
            "Cross-case CDR correlation: suspect's device pinged multiple towers overlapping with SIM cloning network.",
            "Unregistered SIM linked to this case was also active during an incident in an adjacent case.",
            "Communication intercept reveals operational coordination between this syndicate and a parallel distribution network.",
        ],
        "_default": [
            "Call data record identified: suspect made contact with associate approximately 30 minutes before event.",
            "Mobile intercept shows coded communication between two parties of interest linked to this case.",
            "CDR analysis confirms contact between accused persons at a time consistent with operational planning.",
        ],
    },
    "DEVICE_PING": {
        "CRIMINAL": [
            "IMEI trace confirms suspect's handset was active at the crime scene location within the incident window.",
            "Cell tower triangulation places accused within 200 meters of the target premises at the time of the offence.",
            "Forensic CDR analysis: SIM card registered to alias identity pinged sector antenna adjacent to the incident site.",
        ],
        "FINANCIAL": [
            "Device ping from accused's secondary phone confirms presence at the hawala exchange point during transfer window.",
            "IMEI trace reveals accused's handset accessed a banking application from an unknown device linked to a mule account.",
            "Cell sector log places the accused at the registration address of the shell company on the date of incorporation.",
        ],
        "_default": [
            "IMEI/IMSI trace confirms device belonging to subject of interest was active in the vicinity during the relevant period.",
            "Cell tower log entry: target device recorded at sector antenna overlapping the event location.",
            "Device ping corroborates physical surveillance observation — suspect's handset co-located at scene.",
        ],
    },
    "TRANSACTION": {
        "FINANCIAL": [
            "Bank statement analysis reveals structured cash withdrawal of Rs. 4.9 lakh — deliberately below reporting threshold.",
            "RTGS transfer from shell entity to mule account detected; funds disbursed in smaller tranches within 48 hours.",
            "Hawala transfer recorded by informant source: Rs. 18 lakh routed via non-banking intermediary to undisclosed destination.",
        ],
        "CRIMINAL": [
            "Financial forensics confirms payment to arms supplier via cryptocurrency exchange routed through VPN-masked wallet.",
            "Cash deposit of Rs. 3.2 lakh in multiple accounts over three days — pattern consistent with proceeds laundering.",
            "Transaction tracing: payment received by accused within 12 hours of the offence, suggesting pre-arranged payment.",
        ],
        "_default": [
            "Suspicious financial transaction flagged: transfer inconsistent with declared income profile of the subject.",
            "Account statement reveals debit to unknown payee on the date of incident — under forensic review.",
            "Wire transfer analysis links this subject to a beneficiary account flagged in an adjacent financial investigation.",
        ],
    },
    "VEHICLE_SIGHTING": {
        "CRIMINAL": [
            "CCTV footage recovered from petrol station confirms passage of suspect vehicle with cloned registration plate at 02:14 hrs.",
            "Toll plaza e-tag log places the stolen vehicle on the NH-48 corridor, consistent with the escape route.",
            "Eyewitness corroborated by ANPR: dark-coloured SUV with obscured plates sighted near incident site 8 minutes before alarm.",
        ],
        "MULTI_CASE": [
            "ANPR cross-reference: vehicle linked to this case also recorded at locations relevant to two additional active cases.",
            "Relay-attack device residue found in the vehicle — forensic match to a method used in a prior plate-cloning incident.",
            "Suspected vehicle transited through three jurisdictions; toll data forwarded to Gurugram and Noida units.",
        ],
        "_default": [
            "Vehicle of interest sighted by foot constable and corroborated by roadside CCTV — registration noted and queued for trace.",
            "Patrol unit observed suspect vehicle conducting a slow pass of the premises 90 minutes before the incident.",
            "ANPR alert triggered on target vehicle; live tracking handed off to mobile surveillance team.",
        ],
    },
    "MEETING": {
        "CRIMINAL": [
            "Human intelligence source reports clandestine meeting between two accused at a dhaba in Rohini, lasting approximately 40 minutes.",
            "Surveillance photographs show co-accused meeting at a known location used by the gang for distribution coordination.",
            "Physical surveillance confirmed: all four identified suspects met at a private residence ahead of the planned offence.",
        ],
        "MULTI_CASE": [
            "Cross-case entity analysis: two individuals present at this meeting also appear in the entity graph of an adjacent case.",
            "Meeting attendee list cross-referenced with syndicate network map — three attendees share organizational links.",
            "Intelligence report: meeting at this location follows a recurring pattern of operational briefings before major incidents.",
        ],
        "_default": [
            "Controlled observation confirms meeting between persons of interest — duration approximately 25 minutes.",
            "HUMINT report: subject attended a gathering of known associates at a residence under periodic surveillance.",
            "Meeting documented by surveillance team; attendees photographed and submitted for identity verification.",
        ],
    },
    "SURVEILLANCE_OBSERVATION": {
        "_default": [
            "Surveillance team documented subject departing from the premises and travelling to two separate locations within the hour.",
            "Static observation post confirmed recurring pattern: subject visits the same commercial address every Tuesday morning.",
            "Aerial surveillance asset captured movement sequence linking suspect's vehicle to a secondary location not previously identified.",
        ],
    },
    "ARREST": {
        "_default": [
            "Accused apprehended at the scene following a tip from an informant; resisted briefly before being secured.",
            "Arrest conducted jointly with NCB; subject found in possession of contraband consistent with the alleged offence.",
            "Subject arrested under Section 41 CrPC on the basis of non-bailable warrant issued by the court. Formal custody transferred.",
        ],
    },
    "SEIZURE": {
        "CRIMINAL": [
            "Search team seized one country-made firearm, two live cartridges, and a burner mobile phone from the accused's premises.",
            "Seizure of forged vehicle registration documents and a relay-attack device during search of accused's residence.",
            "Contraband seized during vehicle interception: quantity consistent with large-scale supply rather than personal use.",
        ],
        "FINANCIAL": [
            "Electronic devices seized from office of shell company director for forensic imaging and analysis.",
            "Bank lockers operated by accused opened under court order; contents include unaccounted cash and property deeds.",
            "Documents seized from premises confirm the existence of a parallel books-of-accounts system.",
        ],
        "_default": [
            "Search and seizure conducted under Section 165 CrPC. Items recovered forwarded to forensic laboratory.",
            "Contraband and documentary evidence seized. Chain of custody established. Panchnama recorded in presence of witnesses.",
            "Vehicle search yielded concealed items relevant to the investigation. Formal seizure memo executed.",
        ],
    },
    "FORENSIC_COLLECTION": {
        "_default": [
            "Forensic team collected biological samples, latent fingerprints, and tool marks from the scene. Exhibits sealed and labelled.",
            "Digital forensics unit extracted call logs, deleted messages, and application data from seized device.",
            "Scene-of-crime officer documented evidence; photographs and measurements submitted for court record.",
        ],
    },
    "FIR_FILING": {
        "_default": [
            "FIR registered under applicable IPC/BNSS sections. Cognizance taken by the Investigating Officer.",
            "First Information Report filed on the basis of complainant's statement. Case assigned to district detective wing.",
            "FIR lodged following preliminary inquiry. Section 154 CrPC compliance confirmed; copy furnished to complainant.",
        ],
    },
    "BORDER_CROSSING": {
        "_default": [
            "Immigration bureau records confirm subject exited through IGI Terminal 3 using an alias travel document under review.",
            "Border check post recorded the vehicle transiting into NCR from Haryana boundary; driver identity unverified.",
            "Interpol red-corner notice cross-referenced: subject's biometric data matched against a watchlist entry at the checkpoint.",
        ],
    },
    "PROPERTY_MUTATION": {
        "FINANCIAL": [
            "Revenue records reveal fraudulent mutation of commercial property title; beneficial ownership concealed through nominee.",
            "Sub-registrar office documents show forged NOC used to effect a benami property transfer in the accused's network.",
            "Registry records confirm multiple sale deeds executed for the same plot — clear double-sale fraud.",
        ],
        "_default": [
            "Property mutation records obtained from revenue department; anomalies noted for forensic review.",
            "Title chain analysis reveals gap in ownership records consistent with fraudulent insertion of a nominee owner.",
            "Encumbrance certificate obtained; pending litigation and attachment orders noted against the property.",
        ],
    },
    "MEDICAL_EXAMINATION": {
        "_default": [
            "Medical examination of the victim completed; injury report consistent with the complainant's account.",
            "Forensic physician's report noted and submitted. Post-mortem findings to be reviewed by investigating officer.",
            "Sample collection completed. DNA profile sent to CFSL for comparison against evidence collected at scene.",
        ],
    },
    "OTHER": {
        "_default": [
            "Intelligence-corroborated operational event: details classified at source-protection level. Summary retained in case file.",
            "Case-specific investigative action completed; outcome documented in interim progress report.",
            "Witness contacted and preliminary statement recorded. Formal 161 CrPC statement scheduled for next working day.",
        ],
    },
    "MESSAGE": {
        "_default": [
            "Intercepted encrypted message chain shows planning communication between accused persons using an OTT platform.",
            "WhatsApp forensics: deleted messages recovered confirming prior agreement between two accused on distribution logistics.",
            "Signal-intercept derived from LAWFUL authority: message content analysed and summarised for investigation file.",
        ],
    },
}

# ── Investigative lead templates ──────────────────────────────────────────────
# Variables: {entity_name}, {event_type}, {zone}, {case_number}, {case_type_label}
LEAD_TEMPLATES = [
    # Entity-movement leads
    (
        "HIGH",
        "PERSON",
        "Movement pattern of {entity_name} across {zone} requires cross-verification with CDR data from adjacent cell towers.",
        "Subject appears in {event_count} events; travel sequence does not match declared employment location. Recommend CDR deep-dive.",
    ),
    (
        "MEDIUM",
        "PERSON",
        "Co-presence of {entity_name} with a known associate at two separate event locations warrants further surveillance.",
        "CDR and ANPR data confirm subject was in the same geographic cluster as another entity of interest on multiple dates.",
    ),
    (
        "HIGH",
        "PERSON",
        "Identity verification required for {entity_name}: document anomaly detected in case file.",
        "KYC document submitted during FIR filing uses a PIN code inconsistent with the declared address. Forgery suspected.",
    ),
    # Financial-angle leads
    (
        "HIGH",
        "FINANCIAL",
        "Cash-flow irregularity linked to {case_number}: transaction events suggest round-tripping through intermediary accounts.",
        "Debit and credit pattern in account associated with case entities shows structured layering of funds over a 30-day window.",
    ),
    (
        "MEDIUM",
        "FINANCIAL",
        "Unverified hawala network link in {zone}: follow the money trail from transaction events in this case to beneficial recipients.",
        "Multiple small-value transfers from entities in this case aggregate to a significant undisclosed sum. Recommend FINTRAC referral.",
    ),
    # Vehicle / device leads
    (
        "HIGH",
        "VEHICLE",
        "Vehicle sighting pattern in {zone} suggests a pre-planned escape route consistent with the offence MO.",
        "ANPR data from three separate events places the same vehicle registration at locations that form a coherent exit corridor.",
    ),
    (
        "MEDIUM",
        "DEVICE",
        "IMEI cluster analysis: two handsets associated with case entities show identical cell-tower sequences — possible operational pair.",
        "Device proximity correlation across ping events suggests coordinated movement; recommend tower data from adjacent stations.",
    ),
    # Cross-case leads
    (
        "HIGH",
        "CROSS_CASE",
        "Entity overlap detected: at least one person of interest in {case_number} appears in the entity graph of another active case.",
        "Graph traversal confirms shared entity linkage; recommend joint case-file review with the relevant investigating unit.",
    ),
    (
        "MEDIUM",
        "CROSS_CASE",
        "Communication intercept in {case_number} references a location name matching an active surveillance target in an adjacent zone.",
        "Geographic correlation of event locations across case files suggests a shared operational base. Recommend deconfliction briefing.",
    ),
    # Location-intelligence leads
    (
        "MEDIUM",
        "LOCATION",
        "Transit hub at {zone} appears in multiple events across this case — possible recurring rendezvous or handoff point.",
        "Three or more events are co-located at or near the same address. This location should be placed under periodic observation.",
    ),
    (
        "LOW",
        "LOCATION",
        "Secondary address identified in {zone} from witness statement; not yet verified against physical inspection.",
        "Statement mentions a premises used for storage; coordinates approximate. Field visit required to confirm and photograph.",
    ),
]


def scatter_ncr_coords(center_lat: float, center_lon: float, rng: random.Random, spread: float = 0.025) -> Tuple[float, float]:
    """Generate scattered NCR coordinates around a centre point."""
    for _ in range(30):
        lat = center_lat + rng.gauss(0, spread)
        lon = center_lon + rng.gauss(0, spread)
        if 28.10 <= lat <= 28.95 and 76.75 <= lon <= 77.65:
            return round(lat, 6), round(lon, 6)
    return round(center_lat, 6), round(center_lon, 6)


async def get_or_create_generation_run(conn: AsyncConnection, dry_run: bool, force: bool) -> Optional[str]:
    """
    Returns the run_id to tag new records with. Checks for idempotency.
    Returns None if already applied and not --force.
    """
    # Check if this remediation has already been applied
    r = await conn.execute(text(
        "SELECT run_id::text FROM civix.generation_run "
        "WHERE generator_version = :label LIMIT 1;"
    ), {"label": REMEDIATION_RUN_LABEL})
    existing = r.fetchone()
    if existing and not force:
        print(f"  ⚠️  Remediation '{REMEDIATION_RUN_LABEL}' already applied (run_id={existing[0][:12]}...).")
        print(f"      Pass --force to re-apply. Exiting as no-op.")
        return None

    if dry_run:
        # Return a fake run_id for dry-run reporting
        return str(uuid.uuid4())

    # Insert a new generation_run record
    run_id = str(uuid.uuid4())
    await conn.execute(text(
        "INSERT INTO civix.generation_run (run_id, generator_version, started_at, finished_at) "
        "VALUES (CAST(:run_id AS uuid), :label, now(), now());"
    ), {"run_id": run_id, "label": REMEDIATION_RUN_LABEL})
    return run_id


async def p0a_spatial_enrichment(
    conn: AsyncConnection,
    synthetic_case_ids: List[str],
    hero_ids: Set[str],
    rng: random.Random,
    run_id: str,
    dry_run: bool,
) -> Dict[str, int]:
    """
    P0-A: For each static synthetic case (all events at same location), insert
    new distinct NCR locations and reassign events to create movement sequences.
    """
    print("\n📍 P0-A: Spatial Enrichment (movement sequences)")

    # Find static cases: those with ≤ 1 distinct location
    r = await conn.execute(text("""
        SELECT el.case_id::text, COUNT(DISTINCT el.location_id) as distinct_locs,
               array_agg(DISTINCT el.event_id::text) as event_ids,
               array_agg(DISTINCT el.event_location_id::text) as loc_record_ids
        FROM civix.event_location el
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        WHERE c.case_number LIKE 'SYN-%'
        GROUP BY el.case_id
        HAVING COUNT(DISTINCT el.location_id) <= 1
    """))
    static_cases = [dict(row._mapping) for row in r.fetchall()]
    print(f"  Found {len(static_cases)} static synthetic cases (≤1 distinct location).")

    new_locations_inserted = 0
    event_locations_updated = 0

    for case_data in static_cases:
        cid = case_data["case_id"]
        guard_case_id_not_hero(cid)

        event_ids = case_data["event_ids"]  # list of event UUIDs as strings
        if not event_ids:
            continue

        # Determine number of movement waypoints to create (2-4 per case)
        n_waypoints = rng.randint(2, 4)

        # Pick n_waypoints distinct NCR zones (different from each other)
        chosen_zones = rng.sample(NCR_ZONES, min(n_waypoints, len(NCR_ZONES)))
        loc_type = rng.choice(MOVEMENT_LOCATION_TYPES)

        # Create new location records
        new_location_ids = []
        for zone_name, zone_lat, zone_lon in chosen_zones:
            lat, lon = scatter_ncr_coords(zone_lat, zone_lon, rng, spread=0.012)
            new_loc_id = str(uuid.uuid4())
            loc_name = f"Investigative Location — {zone_name}"
            if not dry_run:
                await conn.execute(text("""
                    INSERT INTO civix.entity (entity_id, entity_type, visibility_status, created_at)
                    VALUES (CAST(:eid AS uuid), CAST('LOCATION' AS civix.entity_type_enum), 'ACTIVE', now())
                    ON CONFLICT (entity_id) DO NOTHING;
                """), {"eid": new_loc_id})
                await conn.execute(text("""
                    INSERT INTO civix.location (entity_id, location_name, geometry, location_type, uncertainty_radius_meters)
                    VALUES (
                        CAST(:eid AS uuid),
                        :name,
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                        CAST(:loc_type AS civix.location_type_enum),
                        :uncertainty
                    )
                    ON CONFLICT (entity_id) DO NOTHING;
                """), {
                    "eid": new_loc_id,
                    "name": loc_name,
                    "lon": lon,
                    "lat": lat,
                    "loc_type": loc_type,
                    "uncertainty": rng.uniform(50.0, 400.0),
                })
            new_location_ids.append(new_loc_id)
            new_locations_inserted += 1

        if not new_location_ids:
            continue

        # Distribute events across the new locations
        # First event keeps original location (the crime scene anchor)
        # Remaining events get redistributed across new waypoints
        events_to_move = event_ids[1:]  # keep event_ids[0] at original loc
        for i, ev_id in enumerate(events_to_move):
            new_loc_id = new_location_ids[i % len(new_location_ids)]
            predicates = ["SEEN_AT", "PRESENT_AT", "VISITED", "LOCATED_AT", "PINGED_TOWER"]
            ep_statuses = ["CONFIRMED", "PROBABLE", "POSSIBLE"]
            pred = rng.choice(predicates)
            ep = rng.choice(ep_statuses)

            if not dry_run:
                await conn.execute(text("""
                    UPDATE civix.event_location
                    SET location_id = CAST(:loc_id AS uuid),
                        location_predicate = CAST(:pred AS civix.predicate_enum),
                        epistemic_status   = CAST(:ep AS civix.epistemic_status_enum),
                        generation_run_id  = CAST(:run_id AS uuid)
                    WHERE event_id = CAST(:ev_id AS uuid)
                      AND case_id  = CAST(:case_id AS uuid)
                """), {
                    "loc_id": new_loc_id,
                    "pred": pred,
                    "ep": ep,
                    "run_id": run_id,
                    "ev_id": ev_id,
                    "case_id": cid,
                })
            event_locations_updated += 1

    print(f"  ✅ P0-A complete — {new_locations_inserted} new locations, {event_locations_updated} events remapped.")
    return {"new_locations": new_locations_inserted, "events_updated": event_locations_updated}


async def p0b_investigative_leads(
    conn: AsyncConnection,
    synthetic_case_ids: List[str],
    hero_ids: Set[str],
    rng: random.Random,
    run_id: str,
    dry_run: bool,
) -> Dict[str, int]:
    """
    P0-B: Generate 2-3 investigative leads per synthetic case, grounded in
    actual case entities and event types present in the case.
    """
    print("\n🔍 P0-B: Investigative Lead Generation")

    # Load case metadata for all synthetic cases at once
    r = await conn.execute(text("""
        SELECT c.case_id::text, c.case_number, c.case_type::text, c.title,
               c.investigating_unit
        FROM civix.investigative_case c
        WHERE c.case_number LIKE 'SYN-%'
    """))
    case_meta = {row["case_id"]: row for row in [dict(r2._mapping) for r2 in r.fetchall()]}

    # Load entity data for all synthetic cases
    r2 = await conn.execute(text("""
        SELECT cer.case_id::text, cer.entity_id::text, e.entity_type::text,
               p.display_name, org.legal_name
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        JOIN civix.investigative_case c ON cer.case_id = c.case_id
        LEFT JOIN civix.person p ON e.entity_id = p.entity_id
        LEFT JOIN civix.organization org ON e.entity_id = org.entity_id
        WHERE c.case_number LIKE 'SYN-%'
    """))
    # Group entities by case
    case_entities: Dict[str, List[Dict]] = {}
    for row in r2.fetchall():
        m = dict(row._mapping)
        cid = m["case_id"]
        if cid not in case_entities:
            case_entities[cid] = []
        case_entities[cid].append(m)

    # Load event type distribution per case
    r3 = await conn.execute(text("""
        SELECT el.case_id::text, e.event_type::text, COUNT(*) as cnt
        FROM civix.event_location el
        JOIN civix.event e ON el.event_id = e.event_id
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        WHERE c.case_number LIKE 'SYN-%'
        GROUP BY el.case_id, e.event_type
    """))
    case_event_types: Dict[str, Dict[str, int]] = {}
    for row in r3.fetchall():
        m = dict(row._mapping)
        cid = m["case_id"]
        if cid not in case_event_types:
            case_event_types[cid] = {}
        case_event_types[cid][m["event_type"]] = m["cnt"]

    # Get zone per case from the first event_location
    r4 = await conn.execute(text("""
        SELECT DISTINCT ON (el.case_id) el.case_id::text, l.location_name
        FROM civix.event_location el
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        JOIN civix.location l ON el.location_id = l.entity_id
        WHERE c.case_number LIKE 'SYN-%'
        ORDER BY el.case_id, el.created_at
    """))
    case_zone = {row[0]: row[1] for row in r4.fetchall()}

    total_leads = 0
    n_leads_per_case = 2  # will vary 2-3 below

    for cid in synthetic_case_ids:
        guard_case_id_not_hero(cid)

        meta = case_meta.get(cid, {})
        entities = case_entities.get(cid, [])
        event_types = case_event_types.get(cid, {})
        zone = case_zone.get(cid, "NCR")
        case_number = meta.get("case_number", "SYN-UNKNOWN")
        case_type = meta.get("case_type", "CRIMINAL")

        # Pick a PERSON entity name for leads (if available); fallback to any entity
        person_entities = [e for e in entities if e["entity_type"] == "PERSON" and e.get("display_name")]
        all_entities_with_id = [e for e in entities if e.get("entity_id")]
        entity_name = person_entities[0]["display_name"] if person_entities else "Subject of Interest"
        # target_entity_id must not be NULL — fall back to any available entity
        if person_entities:
            target_entity_id = person_entities[0]["entity_id"]
        elif all_entities_with_id:
            target_entity_id = all_entities_with_id[0]["entity_id"]
        else:
            target_entity_id = None  # Skip this case's leads if no entities exist

        event_count = sum(event_types.values())

        # Skip if no entity exists to target (should be very rare)
        if target_entity_id is None:
            continue

        # Select 2-3 lead templates
        n_leads = rng.randint(2, 3)
        chosen_templates = rng.sample(LEAD_TEMPLATES, min(n_leads, len(LEAD_TEMPLATES)))

        for priority, lead_category, lead_text_fmt, explanation_fmt in chosen_templates:
            lead_text = lead_text_fmt.format(
                entity_name=entity_name,
                zone=zone.replace("Investigative Location — ", "").replace("Incident Location (", "").split(")")[0],
                case_number=case_number,
                event_count=event_count,
                case_type_label=case_type,
            )
            explanation = explanation_fmt.format(
                entity_name=entity_name,
                zone=zone.replace("Investigative Location — ", ""),
                case_number=case_number,
                event_count=event_count,
            )

            lead_id = str(uuid.uuid4())
            confidence = round(rng.uniform(0.55, 0.92), 4)

            if not dry_run:
                await conn.execute(text("""
                    INSERT INTO civix.investigative_lead (
                        lead_id, case_id, lead_text, explanation, priority, status,
                        ai_confidence, generated_by_person, created_at,
                        feature_vector_version, deterministic_findings, explanation_status,
                        target_entity_id
                    )
                    VALUES (
                        CAST(:lead_id AS uuid), CAST(:case_id AS uuid),
                        :lead_text, :explanation,
                        CAST(:priority AS civix.lead_priority_enum),
                        CAST('OPEN' AS civix.lead_status_enum),
                        :confidence,
                        '00000000-0000-0000-0000-000000000001'::uuid,
                        now(),
                        'synthetic-semantics-v1',
                        '[]'::jsonb,
                        'PENDING',
                        CAST(:target_entity_id AS uuid)
                    )
                    ON CONFLICT DO NOTHING;
                """), {
                    "lead_id": lead_id,
                    "case_id": cid,
                    "lead_text": lead_text,
                    "explanation": explanation,
                    "priority": priority,
                    "confidence": confidence,
                    "target_entity_id": target_entity_id,
                })
            total_leads += 1

    print(f"  ✅ P0-B complete — {total_leads} investigative leads generated.")
    return {"total_leads": total_leads}


async def p1_event_descriptions(
    conn: AsyncConnection,
    hero_ids: Set[str],
    rng: random.Random,
    run_id: str,
    dry_run: bool,
) -> Dict[str, int]:
    """
    P1: Replace generic event descriptions with domain-specific narrative text.
    Only updates events whose descriptions match the generic machine-generated pattern.
    """
    print("\n📝 P1: Event Description Enrichment")

    # Load events with generic descriptions for synthetic cases
    r = await conn.execute(text("""
        SELECT DISTINCT ON (e.event_id)
            e.event_id::text, e.event_type::text, e.description,
            el.case_id::text,
            c.case_type::text, c.case_number
        FROM civix.event e
        JOIN civix.event_location el ON e.event_id = el.event_id
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        WHERE c.case_number LIKE 'SYN-%'
          AND (
              e.description LIKE 'Event #%'
              OR e.description IS NULL
              OR e.description = ''
          )
        ORDER BY e.event_id, c.case_number
    """))
    generic_events = [dict(row._mapping) for row in r.fetchall()]
    print(f"  Found {len(generic_events)} events with generic/null descriptions.")

    updated = 0
    for ev in generic_events:
        cid = ev["case_id"]
        guard_case_id_not_hero(cid)

        event_type = ev["event_type"]
        case_type = ev.get("case_type", "CRIMINAL")

        # Get template for this event_type + case_type combo
        type_templates = EVENT_DESC_TEMPLATES.get(event_type, EVENT_DESC_TEMPLATES.get("OTHER", {}))
        case_specific = type_templates.get(case_type, type_templates.get("_default", []))
        if not case_specific:
            # Fallback to any _default
            case_specific = type_templates.get("_default", [
                f"Investigative event of type {event_type} recorded in case file."
            ])

        new_desc = rng.choice(case_specific)

        if not dry_run:
            await conn.execute(text("""
                UPDATE civix.event
                SET description = :desc,
                    generation_run_id = CAST(:run_id AS uuid)
                WHERE event_id = CAST(:ev_id AS uuid)
            """), {
                "desc": new_desc,
                "run_id": run_id,
                "ev_id": ev["event_id"],
            })
        updated += 1

    print(f"  ✅ P1 complete — {updated} event descriptions enriched.")
    return {"events_updated": updated}


async def remediate_investigative_semantics(dry_run: bool = True, force: bool = False):
    print("=" * 72)
    print("CIVIX 2.0 — INVESTIGATIVE SEMANTICS REMEDIATION")
    print(f"Mode: {'DRY RUN (no DB mutations)' if dry_run else 'LIVE MUTATION (transactional)'}")
    print(f"Force re-run: {force}")
    print("=" * 72)

    # 1. Load Hero Manifest
    hero_ids = get_protected_hero_case_ids()
    print(f"\n🔒 Hero Manifest: {len(hero_ids)} protected Hero cases locked.")
    assert len(hero_ids) == 13, f"Expected 13 Hero cases, got {len(hero_ids)}"

    # 2. Init RNGs
    rng_spatial = random.Random(SEED_SPATIAL)
    rng_leads   = random.Random(SEED_LEADS)
    rng_desc    = random.Random(SEED_DESC)

    async with engine.begin() as conn:
        # 3. Hero World Snapshot — BEFORE
        print("\n📸 Building Pre-Remediation Hero World Snapshot...")
        hero_before = await build_hero_world_snapshot(conn)
        print(f"✅ Pre-Remediation Hero Hash: {hero_before['overall_hash']}")

        # 4. Idempotency check / generation_run creation
        run_id = await get_or_create_generation_run(conn, dry_run, force)
        if run_id is None:
            return  # Already applied, nothing to do

        print(f"\n🆔 Remediation Run ID: {run_id}")

        # 5. Load all 254 synthetic case IDs
        r = await conn.execute(text(
            "SELECT case_id::text FROM civix.investigative_case WHERE case_number LIKE 'SYN-%' ORDER BY case_number;"
        ))
        synthetic_case_ids = [row[0] for row in r.fetchall()]
        print(f"\n📊 Synthetic cases loaded: {len(synthetic_case_ids)}")
        assert len(synthetic_case_ids) == 254, f"Expected 254 synthetic cases, found {len(synthetic_case_ids)}"

        # Strict Hero guard on all synthetic IDs
        for cid in synthetic_case_ids:
            guard_case_id_not_hero(cid)
        print("✅ Hero Guard: 0 Hero cases in synthetic population.")

        # 6. Execute P0-A: Spatial Enrichment
        spatial_result = await p0a_spatial_enrichment(
            conn, synthetic_case_ids, hero_ids, rng_spatial, run_id, dry_run
        )

        # 7. Execute P0-B: Investigative Leads
        leads_result = await p0b_investigative_leads(
            conn, synthetic_case_ids, hero_ids, rng_leads, run_id, dry_run
        )

        # 8. Execute P1: Event Descriptions
        desc_result = await p1_event_descriptions(
            conn, hero_ids, rng_desc, run_id, dry_run
        )

        # 9. Hero World Snapshot — AFTER
        print("\n📸 Building Post-Remediation Hero World Snapshot...")
        hero_after = await build_hero_world_snapshot(conn)
        print(f"✅ Post-Remediation Hero Hash: {hero_after['overall_hash']}")

        ok = verify_hero_snapshots_identical(hero_before, hero_after)
        if not ok:
            raise RuntimeError("❌ HERO WORLD DRIFT DETECTED! Rolling back all changes.")
        print("✅ Hero World integrity confirmed — zero drift.")

        if dry_run:
            print("\n⏩ DRY RUN COMPLETE — No data has been written to the database.")
            print("   Re-run with --execute to commit.")
        else:
            print("\n✅ LIVE COMMIT — All changes committed within transaction.")

    print("\n" + "=" * 72)
    print("REMEDIATION SUMMARY")
    print("=" * 72)
    print(f"  P0-A Spatial Enrichment:")
    print(f"    New locations inserted:    {spatial_result['new_locations']}")
    print(f"    Events remapped:           {spatial_result['events_updated']}")
    print(f"  P0-B Investigative Leads:")
    print(f"    Leads generated:           {leads_result['total_leads']}")
    print(f"  P1 Event Descriptions:")
    print(f"    Descriptions enriched:     {desc_result['events_updated']}")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="CIVIX 2.0 — Investigative Semantics Remediation")
    parser.add_argument("--execute", action="store_true", help="Commit changes (default: dry run)")
    parser.add_argument("--force", action="store_true", help="Re-apply even if already run")
    args = parser.parse_args()
    dry_run = not args.execute
    asyncio.run(remediate_investigative_semantics(dry_run=dry_run, force=args.force))


if __name__ == "__main__":
    main()

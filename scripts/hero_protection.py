import os
import sys
import json
import hashlib
from typing import Dict, Any, Set
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Path to the canonical Hero Manifest
MANIFEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "protected_hero_cases.json"))

def load_protected_hero_manifest() -> Dict[str, Any]:
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Hero Manifest file not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH, "r") as f:
        data = json.load(f)
    if data.get("protected_hero_cases_count") != 13 or len(data.get("protected_cases", [])) != 13:
        raise ValueError(f"Hero Manifest MUST contain exactly 13 cases! Found {len(data.get('protected_cases', []))}")
    return data

def get_protected_hero_case_ids() -> Set[str]:
    data = load_protected_hero_manifest()
    hero_ids = {c["case_id"].lower() for c in data["protected_cases"]}
    if len(hero_ids) != 13:
        raise ValueError(f"Duplicate IDs in Hero Manifest! Expected 13 unique IDs, got {len(hero_ids)}")
    return hero_ids

def guard_case_id_not_hero(case_id: str):
    hero_ids = get_protected_hero_case_ids()
    if str(case_id).lower() in hero_ids:
        raise RuntimeError(f"FATAL SECURITY VIOLATION: Attempted mutation on protected Hero Case ID {case_id}!")

async def build_hero_world_snapshot(conn: AsyncConnection) -> Dict[str, Any]:
    """
    Builds a canonical, deterministic SHA-256 snapshot of all database records
    belonging to or connected to the 13 Protected Hero Cases.
    """
    hero_ids = list(get_protected_hero_case_ids())
    hero_ids_str = ", ".join(f"'{hid}'::uuid" for hid in hero_ids)

    snapshot = {}

    # 1. investigative_case
    r = await conn.execute(text(f"""
        SELECT case_id::text, case_number, title, case_type, status, priority, jurisdiction, investigating_unit, opened_at::text, closed_at::text
        FROM civix.investigative_case
        WHERE case_id IN ({hero_ids_str})
        ORDER BY case_id ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["investigative_case"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # 2. case_entity_role
    r = await conn.execute(text(f"""
        SELECT case_id::text, entity_id::text, role
        FROM civix.case_entity_role
        WHERE case_id IN ({hero_ids_str})
        ORDER BY case_id ASC, entity_id ASC, role ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["case_entity_role"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # 3. event_location (anchored events to hero cases)
    r = await conn.execute(text(f"""
        SELECT event_location_id::text, event_id::text, location_id::text, location_predicate, epistemic_status, case_id::text
        FROM civix.event_location
        WHERE case_id IN ({hero_ids_str})
        ORDER BY event_location_id ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["event_location"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # Extract event_ids connected to hero cases
    hero_event_ids = [row["event_id"] for row in rows if row.get("event_id")]
    if hero_event_ids:
        ev_str = ", ".join(f"'{eid}'::uuid" for eid in set(hero_event_ids))
        # 4. event
        r = await conn.execute(text(f"""
            SELECT event_id::text, event_type, occurred_at::text
            FROM civix.event
            WHERE event_id IN ({ev_str})
            ORDER BY event_id ASC;
        """))
        e_rows = [dict(row._mapping) for row in r.fetchall()]
    else:
        e_rows = []
    snapshot["event"] = {
        "count": len(e_rows),
        "hash": hashlib.sha256(json.dumps(e_rows, sort_keys=True).encode()).hexdigest(),
        "rows": e_rows
    }

    # 5. fir
    r = await conn.execute(text(f"""
        SELECT fir_id::text, case_id::text, fir_number, police_station, district, filed_at::text
        FROM civix.fir
        WHERE case_id IN ({hero_ids_str})
        ORDER BY fir_id ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["fir"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # 6. evidence_instance
    r = await conn.execute(text(f"""
        SELECT instance_id::text, artifact_id::text, case_id::text, source_record_id::text
        FROM civix.evidence_instance
        WHERE case_id IN ({hero_ids_str})
        ORDER BY instance_id ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["evidence_instance"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # 7. investigative_lead
    r = await conn.execute(text(f"""
        SELECT lead_id::text, case_id::text, lead_text, priority, status
        FROM civix.investigative_lead
        WHERE case_id IN ({hero_ids_str})
        ORDER BY lead_id ASC;
    """))
    rows = [dict(row._mapping) for row in r.fetchall()]
    snapshot["investigative_lead"] = {
        "count": len(rows),
        "hash": hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
        "rows": rows
    }

    # Overall Hero-World Hash
    combined_hashes = "".join([snapshot[k]["hash"] for k in sorted(snapshot.keys())])
    overall_hash = hashlib.sha256(combined_hashes.encode()).hexdigest()
    snapshot["overall_hash"] = overall_hash

    return snapshot

def verify_hero_snapshots_identical(before: Dict[str, Any], after: Dict[str, Any]) -> bool:
    """
    Verifies that the Hero world snapshot before and after remediation are 100% byte-for-byte identical.
    """
    if before["overall_hash"] != after["overall_hash"]:
        print(f"❌ OVERALL HERO SNAPSHOT HASH MISMATCH!")
        print(f"   BEFORE: {before['overall_hash']}")
        print(f"   AFTER:  {after['overall_hash']}")
        for table in sorted(before.keys()):
            if table == "overall_hash":
                continue
            b_h = before[table]["hash"]
            a_h = after[table]["hash"]
            if b_h != a_h:
                print(f"  ❌ Table '{table}' MISMATCH! Before rows: {before[table]['count']}, After rows: {after[table]['count']}")
        return False
    return True

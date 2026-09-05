"""
database/telecom_benchmark/generator.py

CIVIX 2.0 — Synthetic Telecom Intelligence Benchmark Generator
Version: telecom-benchmark-v1
Tier: 1 (100-500 events per case)

ISOLATION GUARANTEES:
  - Writes ONLY to civix_telecom_benchmark.* (fully qualified)
  - NEVER writes to civix.* schema
  - No dynamic search_path changes
  - No cross-schema foreign keys created
  - Hero cases from manifest are verified and protected
  - Primary schema counts verified before and after

SAFETY MECHANISMS:
  1. Database identity check — must be civix_demo
  2. Hero manifest loaded from protected_hero_cases.json
  3. Primary baseline counts captured before any write
  4. Benchmark writes isolated to civix_telecom_benchmark schema
  5. Post-generation verification compares baseline vs final
  6. Hard fail on any safety violation

Usage:
  python database/telecom_benchmark/generator.py
  python database/telecom_benchmark/generator.py --tier 1
  python database/telecom_benchmark/generator.py --list-runs
"""

import argparse
import asyncio
import json
import math
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

# Force UTF-8 output on Windows to prevent cp1252 encoding errors
if sys.stdout.encoding != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


from faker import Faker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncConnection
from sqlalchemy import text

# ─── Configuration ────────────────────────────────────────────────────────────

EXPECTED_DATABASE = "civix_demo"
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"
MANIFEST_PATH = Path(__file__).parent.parent / "protected_hero_cases.json"
GENERATOR_VERSION = "telecom-benchmark-v1"
PROVENANCE = "SYNTHETIC_TELECOM_BENCHMARK"
DETERMINISTIC_SEED = 20260905  # Reproducible every run

# Tier 1 density
TIER1_EVENTS_PER_CASE = 300

# Delhi NCR tower grid — geographically coherent synthetic coverage
DELHI_NCR_TOWERS = [
    # Central Delhi
    {"code": "TOWER-CP-01",  "name": "Connaught Place Central",     "lat": 28.6315, "lon": 77.2167, "area": "Central Delhi"},
    {"code": "TOWER-CP-02",  "name": "Connaught Place East",        "lat": 28.6300, "lon": 77.2200, "area": "Central Delhi"},
    {"code": "TOWER-CC-01",  "name": "Chandni Chowk North",         "lat": 28.6562, "lon": 77.2310, "area": "Old Delhi"},
    {"code": "TOWER-CC-02",  "name": "Chandni Chowk South",         "lat": 28.6500, "lon": 77.2280, "area": "Old Delhi"},
    # Dwarka
    {"code": "TOWER-DW-01",  "name": "Dwarka Sector 10 Alpha",      "lat": 28.5921, "lon": 77.0460, "area": "Dwarka"},
    {"code": "TOWER-DW-02",  "name": "Dwarka Sector 10 Beta",       "lat": 28.5895, "lon": 77.0490, "area": "Dwarka"},
    {"code": "TOWER-DW-03",  "name": "Dwarka Sector 23 North",      "lat": 28.5667, "lon": 77.0540, "area": "Dwarka"},
    {"code": "TOWER-DW-04",  "name": "Dwarka Sector 23 South",      "lat": 28.5640, "lon": 77.0560, "area": "Dwarka"},
    # Rohini
    {"code": "TOWER-RH-01",  "name": "Rohini Sector 3",             "lat": 28.7316, "lon": 77.1209, "area": "Rohini"},
    {"code": "TOWER-RH-02",  "name": "Rohini Sector 9 East",        "lat": 28.7245, "lon": 77.1280, "area": "Rohini"},
    {"code": "TOWER-RH-03",  "name": "Rohini Sector 16",            "lat": 28.7180, "lon": 77.1190, "area": "Rohini"},
    # Najafgarh
    {"code": "TOWER-NJ-01",  "name": "Najafgarh Market Hub",        "lat": 28.6092, "lon": 76.9800, "area": "Najafgarh"},
    {"code": "TOWER-NJ-02",  "name": "Najafgarh Highway East",      "lat": 28.6100, "lon": 76.9950, "area": "Najafgarh"},
    # NH-48 / IGI
    {"code": "TOWER-NH-01",  "name": "NH-48 Km 12 North",          "lat": 28.5962, "lon": 77.0680, "area": "NH-48"},
    {"code": "TOWER-NH-02",  "name": "NH-48 Km 18 South",          "lat": 28.5540, "lon": 77.0720, "area": "NH-48"},
    {"code": "TOWER-IGI-01", "name": "IGI Airport Terminal 2",      "lat": 28.5562, "lon": 77.0988, "area": "IGI Airport"},
    # Noida
    {"code": "TOWER-NO-01",  "name": "Noida Sector 18",             "lat": 28.5704, "lon": 77.3219, "area": "Noida"},
    {"code": "TOWER-NO-02",  "name": "Noida Sector 62",             "lat": 28.6269, "lon": 77.3643, "area": "Noida"},
    # Gurugram
    {"code": "TOWER-GG-01",  "name": "Gurugram Sector 29",          "lat": 28.4744, "lon": 77.0830, "area": "Gurugram"},
    {"code": "TOWER-GG-02",  "name": "MG Road Gurugram",            "lat": 28.4801, "lon": 77.0918, "area": "Gurugram"},
]

OPERATORS = ["Airtel", "Jio", "Vi", "BSNL"]


# ─── Safety Gate ──────────────────────────────────────────────────────────────

async def verify_database_identity(conn: AsyncConnection) -> str:
    """HARD FAIL if not connected to civix_demo."""
    r = await conn.execute(text("SELECT current_database()"))
    actual_db = r.scalar()
    if actual_db != EXPECTED_DATABASE:
        raise RuntimeError(
            f"HARD FAIL: Connected to '{actual_db}', expected '{EXPECTED_DATABASE}'. "
            "Aborting to protect unknown database."
        )
    print(f"[SAFETY] Database identity verified: {actual_db} [OK]")
    return actual_db


def load_hero_manifest() -> dict:
    """Load the authoritative protected Hero cases manifest."""
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"HARD FAIL: Hero manifest not found at {MANIFEST_PATH}")
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    hero_ids = {c["case_id"] for c in manifest["protected_cases"]}
    hero_numbers = {c["case_number"] for c in manifest["protected_cases"]}
    expected_count = manifest["protected_hero_cases_count"]
    assert len(hero_ids) == expected_count, (
        f"HARD FAIL: Manifest claims {expected_count} heroes, but has {len(hero_ids)} unique IDs."
    )
    print(f"[SAFETY] Hero manifest loaded: {expected_count} protected cases [OK]")
    print(f"[SAFETY]   CIV-* cases: {sum(1 for n in hero_numbers if n.startswith('CIV-'))}")
    print(f"[SAFETY]   Other cases: {sum(1 for n in hero_numbers if not n.startswith('CIV-'))}")
    return {"ids": hero_ids, "numbers": hero_numbers, "count": expected_count}


async def capture_primary_baseline(conn: AsyncConnection) -> dict:
    """Capture row counts from civix.* tables for before/after comparison."""
    tables = [
        "investigative_case", "event", "event_participant", "event_location",
        "entity", "phone_number", "sim", "device", "location",
        "sim_in_device", "sim_number_assignment", "case_entity_role"
    ]
    baseline = {}
    for t in tables:
        r = await conn.execute(text(f"SELECT COUNT(*) FROM civix.{t}"))
        baseline[t] = r.scalar()
    print(f"[PREFLIGHT] Primary baseline captured: {baseline['event']} events, "
          f"{baseline['investigative_case']} cases, {baseline['entity']} entities")
    return baseline


async def verify_primary_unchanged(conn: AsyncConnection, baseline: dict) -> bool:
    """Compare current primary counts to baseline. HARD FAIL on any change."""
    ok = True
    for table, expected in baseline.items():
        r = await conn.execute(text(f"SELECT COUNT(*) FROM civix.{table}"))
        actual = r.scalar()
        if actual != expected:
            print(f"[HARD FAIL] civix.{table}: expected {expected}, got {actual}. PRIMARY DATA MUTATED!")
            ok = False
    if ok:
        print("[VERIFICATION] Primary CIVIX schema unchanged [OK]")
    return ok


async def verify_hero_unchanged(conn: AsyncConnection, hero: dict) -> bool:
    """Re-verify all 13 Hero cases exist with correct numbers."""
    ok = True
    for case_num in hero["numbers"]:
        r = await conn.execute(
            text("SELECT COUNT(*) FROM civix.investigative_case WHERE case_number = :num"),
            {"num": case_num}
        )
        if r.scalar() == 0:
            print(f"[HARD FAIL] Hero case '{case_num}' is MISSING from primary DB!")
            ok = False
    if ok:
        print(f"[VERIFICATION] All {hero['count']} Hero cases intact [OK]")
    return ok


# ─── Schema Creation ──────────────────────────────────────────────────────────

async def apply_schema(conn: AsyncConnection) -> None:
    """Apply the benchmark schema DDL. Idempotent (IF NOT EXISTS)."""
    import re
    schema_path = Path(__file__).parent / "schema.sql"
    ddl = schema_path.read_text(encoding="utf-8")
    # Strip block comments (/* ... */)
    ddl = re.sub(r'/\*.*?\*/', '', ddl, flags=re.DOTALL)
    # Strip line comments (-- ...)
    ddl = re.sub(r'--[^\n]*', '', ddl)
    # Split on semicolons, filter blanks
    statements = [s.strip() for s in ddl.split(";") if s.strip()]
    for stmt in statements:
        await conn.execute(text(stmt))
    await conn.commit()
    print("[PHASE 2] Benchmark schema applied [OK]")


async def clear_benchmark_tier_cases(conn: AsyncConnection, case_numbers: list[str]) -> None:
    """Idempotent reset of events/cases for the target benchmark cases."""
    print(f"[PHASE 3] Safely clearing existing data for {case_numbers}...")
    
    # Get generation runs for these cases to clean up unlinked data
    runs_result = await conn.execute(text("""
        SELECT DISTINCT generation_run_id FROM civix_telecom_benchmark.benchmark_case
        WHERE case_number = ANY(:cns)
    """), {"cns": case_numbers})
    runs = [r[0] for r in runs_result.fetchall()]
    
    if not runs:
        return

    # Delete events
    await conn.execute(text("""
        DELETE FROM civix_telecom_benchmark.benchmark_event
        WHERE case_id IN (SELECT id FROM civix_telecom_benchmark.benchmark_case WHERE case_number = ANY(:cns))
    """), {"cns": case_numbers})
    
    # Delete cross case links
    await conn.execute(text("""
        DELETE FROM civix_telecom_benchmark.benchmark_cross_case_link
        WHERE case_a_id IN (SELECT id FROM civix_telecom_benchmark.benchmark_case WHERE case_number = ANY(:cns))
           OR case_b_id IN (SELECT id FROM civix_telecom_benchmark.benchmark_case WHERE case_number = ANY(:cns))
    """), {"cns": case_numbers})
    
    # Delete sim device links generated in these runs
    await conn.execute(text("""
        DELETE FROM civix_telecom_benchmark.benchmark_sim_device_link
        WHERE generation_run_id = ANY(:runs)
    """), {"runs": runs})
    
    # Delete the cases
    await conn.execute(text("""
        DELETE FROM civix_telecom_benchmark.benchmark_case
        WHERE case_number = ANY(:cns)
    """), {"cns": case_numbers})

# ─── Scenario Generators ──────────────────────────────────────────────────────

class BenchmarkContext:
    """Shared state for a generation run."""
    def __init__(self, run_id: str, towers: list[dict], rng: random.Random, fake: Faker):
        self.run_id = run_id
        self.towers = towers  # list of tower dicts with DB `id` attached
        self.rng = rng
        self.fake = fake
        # Entity pools, keyed by MSISDN/IMEI/ICCID for dedup
        self.phones: dict[str, str] = {}    # msisdn -> DB id
        self.devices: dict[str, str] = {}   # imei    -> DB id
        self.sims: dict[str, str] = {}      # iccid   -> DB id


def _tower_by_area(ctx: BenchmarkContext, area: str) -> dict:
    """Return a random tower from a given area."""
    candidates = [t for t in ctx.towers if t["area"] == area]
    return ctx.rng.choice(candidates) if candidates else ctx.rng.choice(ctx.towers)


def _nearby_tower(ctx: BenchmarkContext, tower: dict, max_km: float = 8.0) -> dict:
    """Return a geographically nearby tower (within max_km)."""
    def haversine(t1, t2):
        R = 6371
        dlat = math.radians(t2["lat"] - t1["lat"])
        dlon = math.radians(t2["lon"] - t1["lon"])
        a = math.sin(dlat/2)**2 + math.cos(math.radians(t1["lat"])) * math.cos(math.radians(t2["lat"])) * math.sin(dlon/2)**2
        return R * 2 * math.asin(math.sqrt(a))
    candidates = [t for t in ctx.towers if t["code"] != tower["code"] and haversine(tower, t) <= max_km]
    return ctx.rng.choice(candidates) if candidates else ctx.rng.choice(ctx.towers)


async def ensure_phone(conn: AsyncConnection, ctx: BenchmarkContext, msisdn: str | None = None) -> str:
    """Insert or retrieve a benchmark phone. Returns DB id (str)."""
    if msisdn is None:
        # Generate deterministic BENCH-prefixed MSISDN
        num = ctx.rng.randint(9800000000, 9899999999)
        msisdn = f"98{num % 100000000:08d}"
        # Guarantee unique
        while msisdn in ctx.phones:
            num = ctx.rng.randint(9800000000, 9899999999)
            msisdn = f"98{num % 100000000:08d}"
    if msisdn in ctx.phones:
        return ctx.phones[msisdn]
    phone_id = str(uuid.uuid4())
    await conn.execute(text("""
        INSERT INTO civix_telecom_benchmark.benchmark_phone
            (id, msisdn, operator, circle, synthetic_flag, provenance, generation_run_id)
        VALUES (:id, :msisdn, :op, 'Delhi', TRUE, :prov, :run_id)
        ON CONFLICT (msisdn) DO NOTHING
    """), {"id": phone_id, "msisdn": msisdn, "op": ctx.rng.choice(OPERATORS),
           "prov": PROVENANCE, "run_id": ctx.run_id})
    
    r = await conn.execute(text("SELECT id FROM civix_telecom_benchmark.benchmark_phone WHERE msisdn = :m"), {"m": msisdn})
    actual_id = str(r.scalar())
    ctx.phones[msisdn] = actual_id
    return actual_id


async def ensure_device(conn: AsyncConnection, ctx: BenchmarkContext, imei: str | None = None) -> str:
    """Insert or retrieve a benchmark device."""
    if imei is None:
        imei = f"BENCH-IMEI-{ctx.rng.randint(10000, 99999)}"
    if imei in ctx.devices:
        return ctx.devices[imei]
    dev_id = str(uuid.uuid4())
    manufacturers = ["Samsung", "Xiaomi", "OnePlus", "Realme", "Oppo", "Nokia"]
    await conn.execute(text("""
        INSERT INTO civix_telecom_benchmark.benchmark_device
            (id, imei, manufacturer, model, synthetic_flag, provenance, generation_run_id)
        VALUES (:id, :imei, :mfr, :model, TRUE, :prov, :run_id)
        ON CONFLICT (imei) DO NOTHING
    """), {"id": dev_id, "imei": imei, "mfr": ctx.rng.choice(manufacturers),
           "model": f"Model-{ctx.rng.randint(100, 999)}", "prov": PROVENANCE, "run_id": ctx.run_id})
    
    r = await conn.execute(text("SELECT id FROM civix_telecom_benchmark.benchmark_device WHERE imei = :i"), {"i": imei})
    actual_id = str(r.scalar())
    ctx.devices[imei] = actual_id
    return actual_id


async def ensure_sim(conn: AsyncConnection, ctx: BenchmarkContext, iccid: str | None = None) -> str:
    """Insert or retrieve a benchmark SIM."""
    if iccid is None:
        iccid = f"BENCH-SIM-{ctx.rng.randint(10000, 99999)}"
    if iccid in ctx.sims:
        return ctx.sims[iccid]
    sim_id = str(uuid.uuid4())
    imsi = f"40470{ctx.rng.randint(1000000, 9999999)}"
    await conn.execute(text("""
        INSERT INTO civix_telecom_benchmark.benchmark_sim
            (id, iccid, imsi, issuing_operator, synthetic_flag, provenance, generation_run_id)
        VALUES (:id, :iccid, :imsi, :op, TRUE, :prov, :run_id)
        ON CONFLICT (iccid) DO NOTHING
    """), {"id": sim_id, "iccid": iccid, "imsi": imsi, "op": ctx.rng.choice(OPERATORS),
           "prov": PROVENANCE, "run_id": ctx.run_id})
    
    r = await conn.execute(text("SELECT id FROM civix_telecom_benchmark.benchmark_sim WHERE iccid = :i"), {"i": iccid})
    actual_id = str(r.scalar())
    ctx.sims[iccid] = actual_id
    return actual_id


async def insert_event(conn: AsyncConnection, ctx: BenchmarkContext, case_id: str,
                       event_type: str, occurred_at: datetime, tower_id: str,
                       caller_id: str | None = None, callee_id: str | None = None,
                       subject_id: str | None = None, device_id: str | None = None,
                       sim_id: str | None = None, duration: int | None = None,
                       description: str | None = None) -> str:
    ev_id = str(uuid.uuid4())
    await conn.execute(text("""
        INSERT INTO civix_telecom_benchmark.benchmark_event
            (id, case_id, event_type, occurred_at, duration_seconds,
             caller_phone_id, callee_phone_id, subject_phone_id,
             device_id, sim_id, tower_id, description,
             synthetic_flag, provenance, generation_run_id)
        VALUES
            (:id, :case_id, :etype, :oat, :dur,
             :caller, :callee, :subject,
             :device, :sim, :tower, :desc,
             TRUE, :prov, :run_id)
    """), {
        "id": ev_id, "case_id": case_id, "etype": event_type, "oat": occurred_at,
        "dur": duration, "caller": caller_id, "callee": callee_id, "subject": subject_id,
        "device": device_id, "sim": sim_id, "tower": tower_id, "desc": description,
        "prov": PROVENANCE, "run_id": ctx.run_id
    })
    return ev_id


# ─── Scenario A: Suspect Movement ────────────────────────────────────────────

async def generate_suspect_movement(conn: AsyncConnection, ctx: BenchmarkContext,
                                    case_id: str, base_time: datetime,
                                    n_phones: int = 3, pings_per_phone: int = 40) -> int:
    """
    Generate a suspect (+ associates) moving across geographically coherent tower sequence.
    Returns total events inserted.
    """
    total = 0
    for i in range(n_phones):
        phone_id = await ensure_phone(conn, ctx)
        device_id = await ensure_device(conn, ctx)
        sim_id = await ensure_sim(conn, ctx)

        # Start at a random tower, then move geographically
        current_tower = ctx.rng.choice(ctx.towers)
        t = base_time + timedelta(minutes=ctx.rng.randint(0, 30))

        for ping in range(pings_per_phone):
            # Occasionally move to a nearby tower (realistic dwell)
            if ping % ctx.rng.randint(4, 8) == 0:
                current_tower = _nearby_tower(ctx, current_tower)

            duration = ctx.rng.randint(30, 300) if ctx.rng.random() < 0.4 else None
            etype = "CALL" if duration else "DEVICE_PING"

            callee_id = None
            if etype == "CALL":
                callee_id = await ensure_phone(conn, ctx)

            await insert_event(conn, ctx, case_id, etype, t, current_tower["id"],
                               caller_id=phone_id if etype == "CALL" else None,
                               callee_id=callee_id,
                               subject_id=phone_id if etype == "DEVICE_PING" else None,
                               device_id=device_id, sim_id=sim_id, duration=duration,
                               description=f"BENCH-MOVEMENT: Suspect {i+1} ping at {current_tower['code']}")
            total += 1
            # Advance time: 3-15 minutes per ping
            t += timedelta(minutes=ctx.rng.randint(3, 15))

    return total


# ─── Scenario B: Common Tower Overlap / Co-Location ──────────────────────────

async def generate_co_location(conn: AsyncConnection, ctx: BenchmarkContext,
                               case_id: str, base_time: datetime,
                               n_phones: int = 4, overlap_tower: dict | None = None,
                               total_pings: int = 80) -> int:
    """
    Generate multiple phones overlapping at the same tower in the same time window.
    """
    if overlap_tower is None:
        overlap_tower = ctx.rng.choice(ctx.towers)

    phones = [await ensure_phone(conn, ctx) for _ in range(n_phones)]
    devices = [await ensure_device(conn, ctx) for _ in range(n_phones)]
    sims = [await ensure_sim(conn, ctx) for _ in range(n_phones)]
    total = 0

    # Create an overlap window (2-hour window)
    overlap_start = base_time + timedelta(hours=ctx.rng.randint(0, 4))

    for ev_idx in range(total_pings):
        # Pick a random phone from the group
        idx = ev_idx % n_phones
        phone_id = phones[idx]
        device_id = devices[idx]
        sim_id = sims[idx]

        # All events fall within the overlap tower/window ±20 minutes
        t = overlap_start + timedelta(minutes=ctx.rng.randint(0, 120))

        callee_id = None
        etype = "CALL" if ctx.rng.random() < 0.35 else "DEVICE_PING"
        duration = ctx.rng.randint(20, 180) if etype == "CALL" else None
        if etype == "CALL":
            callee_id = await ensure_phone(conn, ctx)

        # Occasionally ping a nearby tower for noise
        tower = overlap_tower if ctx.rng.random() < 0.75 else _nearby_tower(ctx, overlap_tower, max_km=2.0)

        await insert_event(conn, ctx, case_id, etype, t, tower["id"],
                           caller_id=phone_id if etype == "CALL" else None,
                           callee_id=callee_id,
                           subject_id=phone_id if etype == "DEVICE_PING" else None,
                           device_id=device_id, sim_id=sim_id, duration=duration,
                           description=f"BENCH-COLOC: Group ping at {tower['code']}")
        total += 1

    return total


# ─── Scenario C: SIM/IMEI Reuse ──────────────────────────────────────────────

async def generate_sim_imei_reuse(conn: AsyncConnection, ctx: BenchmarkContext,
                                  case_id: str, base_time: datetime,
                                  n_devices: int = 3, pings_per_device: int = 30) -> int:
    """
    One SIM moves across multiple devices. One device hosts multiple SIMs.
    Creates entries in benchmark_sim_device_link for SIM Analysis tab.
    """
    # The "travelling SIM"
    itinerant_sim_id = await ensure_sim(conn, ctx)
    itinerant_sim_iccid = [k for k, v in ctx.sims.items() if v == itinerant_sim_id][0]

    devices = [await ensure_device(conn, ctx) for _ in range(n_devices)]
    imeis = [k for k, v in ctx.devices.items() if v in devices]
    phones = [await ensure_phone(conn, ctx) for _ in range(n_devices)]
    total = 0

    # Build temporal SIM-in-device history
    window_start = base_time
    for i, device_id in enumerate(devices):
        window_end = window_start + timedelta(hours=ctx.rng.randint(4, 12))

        # Insert SIM-device link
        await conn.execute(text("""
            INSERT INTO civix_telecom_benchmark.benchmark_sim_device_link
                (id, sim_id, device_id, phone_id, valid_from, valid_to,
                 synthetic_flag, provenance, generation_run_id)
            VALUES (:id, :sim, :dev, :phone, :vf, :vt, TRUE, :prov, :run_id)
        """), {"id": str(uuid.uuid4()), "sim": itinerant_sim_id, "dev": device_id,
               "phone": phones[i], "vf": window_start, "vt": window_end,
               "prov": PROVENANCE, "run_id": ctx.run_id})

        # Generate events during this device's active window
        t = window_start
        for _ in range(pings_per_device):
            tower = ctx.rng.choice(ctx.towers)
            etype = "CALL" if ctx.rng.random() < 0.4 else "DEVICE_PING"
            duration = ctx.rng.randint(20, 180) if etype == "CALL" else None
            callee_id = None
            if etype == "CALL":
                callee_id = await ensure_phone(conn, ctx)

            await insert_event(conn, ctx, case_id, etype, t, tower["id"],
                               caller_id=phones[i] if etype == "CALL" else None,
                               callee_id=callee_id,
                               subject_id=phones[i] if etype == "DEVICE_PING" else None,
                               device_id=device_id, sim_id=itinerant_sim_id, duration=duration,
                               description=f"BENCH-SIMSWAP: SIM {itinerant_sim_iccid} in device {i+1}")
            total += 1
            t += timedelta(minutes=ctx.rng.randint(5, 20))

        window_start = window_end + timedelta(minutes=ctx.rng.randint(10, 60))

    return total


# ─── Scenario D: Cross-Case Link ─────────────────────────────────────────────

async def create_cross_case_links(conn: AsyncConnection, ctx: BenchmarkContext,
                                  case_a_id: str, case_b_id: str,
                                  shared_phones: list[str], shared_devices: list[str],
                                  run_id: str) -> None:
    """Register cross-case entity links in the dedicated link table."""
    for phone_id in shared_phones:
        await conn.execute(text("""
            INSERT INTO civix_telecom_benchmark.benchmark_cross_case_link
                (id, case_a_id, case_b_id, entity_type, entity_id,
                 link_note, synthetic_flag, provenance, generation_run_id)
            VALUES (:id, :ca, :cb, 'PHONE', :eid,
                    'Shared phone observed across cases',
                    TRUE, :prov, :run_id)
        """), {"id": str(uuid.uuid4()), "ca": case_a_id, "cb": case_b_id,
               "eid": phone_id, "prov": PROVENANCE, "run_id": run_id})

    for dev_id in shared_devices:
        await conn.execute(text("""
            INSERT INTO civix_telecom_benchmark.benchmark_cross_case_link
                (id, case_a_id, case_b_id, entity_type, entity_id,
                 link_note, synthetic_flag, provenance, generation_run_id)
            VALUES (:id, :ca, :cb, 'DEVICE', :eid,
                    'Shared device observed across cases',
                    TRUE, :prov, :run_id)
        """), {"id": str(uuid.uuid4()), "ca": case_a_id, "cb": case_b_id,
               "eid": dev_id, "prov": PROVENANCE, "run_id": run_id})


# ─── Case Creation ────────────────────────────────────────────────────────────

async def create_benchmark_case(conn: AsyncConnection, run_id: str,
                                case_number: str, title: str, description: str,
                                scenario_type: str, start_time: datetime,
                                end_time: datetime) -> str:
    case_id = str(uuid.uuid4())
    await conn.execute(text("""
        INSERT INTO civix_telecom_benchmark.benchmark_case
            (id, case_number, title, description, scenario_type, severity,
             start_time, end_time, synthetic_flag, provenance, generation_run_id)
        VALUES
            (:id, :cn, :title, :desc, :stype, 'HIGH',
             :st, :et, TRUE, :prov, :run_id)
    """), {"id": case_id, "cn": case_number, "title": title, "desc": description,
           "stype": scenario_type, "st": start_time, "et": end_time,
           "prov": PROVENANCE, "run_id": run_id})
    return case_id


# ─── Tower Seeding ────────────────────────────────────────────────────────────

async def seed_towers(conn: AsyncConnection, run_id: str) -> list[dict]:
    """Insert all tower definitions. Returns list with DB id attached."""
    seeded = []
    for t in DELHI_NCR_TOWERS:
        tower_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO civix_telecom_benchmark.benchmark_tower
                (id, tower_code, name, lat, lon, area, coverage_radius_m,
                 synthetic_flag, provenance, generation_run_id)
            VALUES (:id, :code, :name, :lat, :lon, :area, 500,
                    TRUE, :prov, :run_id)
            ON CONFLICT (tower_code) DO NOTHING
        """), {"id": tower_id, "code": t["code"], "name": t["name"],
               "lat": t["lat"], "lon": t["lon"], "area": t["area"],
               "prov": PROVENANCE, "run_id": run_id})
        # Re-fetch actual id in case ON CONFLICT fired
        r = await conn.execute(text(
            "SELECT id FROM civix_telecom_benchmark.benchmark_tower WHERE tower_code = :code"
        ), {"code": t["code"]})
        actual_id = str(r.scalar())
        seeded.append({**t, "id": actual_id})
    print(f"[PHASE 3] Seeded {len(seeded)} synthetic towers [OK]")
    return seeded


# ─── Verification Report ─────────────────────────────────────────────────────

async def produce_verification_report(conn: AsyncConnection, run_id: str,
                                      hero: dict, baseline_before: dict) -> dict:
    """Compile the full validation report."""
    report: dict[str, Any] = {"generation_run_id": run_id}

    # Primary counts after
    tables = list(baseline_before.keys())
    after = {}
    primary_changed = False
    for t in tables:
        r = await conn.execute(text(f"SELECT COUNT(*) FROM civix.{t}"))
        after[t] = r.scalar()
        if after[t] != baseline_before[t]:
            primary_changed = True

    report["primary_civix_changed"] = primary_changed
    report["primary_counts_before"] = baseline_before
    report["primary_counts_after"] = after

    # Hero check
    hero_intact = True
    for cn in hero["numbers"]:
        r = await conn.execute(
            text("SELECT COUNT(*) FROM civix.investigative_case WHERE case_number = :n"),
            {"n": cn}
        )
        if r.scalar() == 0:
            hero_intact = False
    report["hero_intact"] = hero_intact
    report["hero_count_expected"] = hero["count"]

    # Benchmark counts
    def bcount(table):
        return None  # populated below via async

    for tbl in ["benchmark_case", "benchmark_event", "benchmark_tower",
                "benchmark_phone", "benchmark_device", "benchmark_sim",
                "benchmark_sim_device_link", "benchmark_cross_case_link"]:
        r = await conn.execute(text(f"SELECT COUNT(*) FROM civix_telecom_benchmark.{tbl}"))
        report[f"benchmark_{tbl}_count"] = r.scalar()

    # Provenance check
    r = await conn.execute(text(
        "SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event WHERE provenance != 'SYNTHETIC_TELECOM_BENCHMARK'"
    ))
    bad_prov = r.scalar()
    report["benchmark_provenance_violations"] = bad_prov

    r = await conn.execute(text(
        "SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event WHERE synthetic_flag != TRUE"
    ))
    report["benchmark_synthetic_flag_violations"] = r.scalar()

    return report


# ─── Main Entry Point ─────────────────────────────────────────────────────────

async def run_generation(tier: int = 1):
    print("=" * 60)
    print("CIVIX 2.0 — TELECOM BENCHMARK GENERATOR")
    print(f"Version: {GENERATOR_VERSION}")
    
    if tier == 2:
        t1_phones, t1_pings = 10, 120  # 1200 events
        t1_sims, t1_sim_pings = 5, 60  # 300 events
        t2_phones, t2_pings = 12, 1500 # 1500 events
        print(f"Tier: 2 (Target ~1500 events/case)")
    else:
        t1_phones, t1_pings = 4, 35
        t1_sims, t1_sim_pings = 3, 25
        t2_phones, t2_pings = 5, 120
        print(f"Tier: 1 (Target ~150-300 events/case)")
        
    print(f"Seed: {DETERMINISTIC_SEED}")
    print("=" * 60)

    # ── Safety: Load Hero manifest first ──
    hero = load_hero_manifest()

    # ── Connect ──
    engine = create_async_engine(DB_URL, echo=False)

    async with engine.begin() as conn:
        # ── Safety: Verify DB identity ──
        await verify_database_identity(conn)

        # ── Safety: Capture primary baseline ──
        baseline_before = await capture_primary_baseline(conn)
        hero_ok_before = await verify_hero_unchanged(conn, hero)
        if not hero_ok_before:
            raise RuntimeError("HARD FAIL: Hero cases missing from DB before generation even starts!")

    # ── Phase 2: Apply schema (separate transaction) ──
    print("\n[PHASE 2] Applying benchmark schema...")
    async with engine.begin() as conn:
        await verify_database_identity(conn)
        await apply_schema(conn)

    # ── Phase 3: Generate Tier 1 data ──
    print("\n[PHASE 3] Generating Tier 1 benchmark data...")

    # Create generation run record
    run_id = str(uuid.uuid4())
    rng = random.Random(DETERMINISTIC_SEED)
    fake = Faker("en_IN")
    fake.seed_instance(DETERMINISTIC_SEED)

    async with engine.begin() as conn:
        await verify_database_identity(conn)

        # Register generation run
        await conn.execute(text("""
            INSERT INTO civix_telecom_benchmark.generation_run
                (generation_run_id, seed, tier, generator_version, provenance, notes)
            VALUES (:run_id, :seed, :tier, :ver, :prov, :notes)
        """), {"run_id": run_id, "seed": DETERMINISTIC_SEED, "tier": tier, "ver": GENERATOR_VERSION,
               "prov": PROVENANCE, "notes": f"Tier {tier} — BENCH-TELECOM-001 + BENCH-TELECOM-002"})
        print(f"[PHASE 3] Generation run registered: {run_id}")

        # Idempotent reset for BENCH-TELECOM-001 and 002
        await clear_benchmark_tier_cases(conn, ["BENCH-TELECOM-001", "BENCH-TELECOM-002"])

        # Seed towers
        ctx_towers = await seed_towers(conn, run_id)
        ctx = BenchmarkContext(run_id=run_id, towers=ctx_towers, rng=rng, fake=fake)

        # ── BENCH-TELECOM-001: SUSPECT_MOVEMENT + SIM_IMEI_REUSE ──
        print("\n[PHASE 3] Creating BENCH-TELECOM-001...")
        base_dt_001 = datetime(2026, 3, 14, 2, 0, 0, tzinfo=timezone.utc)
        case1_id = await create_benchmark_case(
            conn, run_id,
            "BENCH-TELECOM-001",
            "Dwarka Movement & SIM Swap Investigation",
            "Synthetic scenario: suspect travels across Dwarka and Najafgarh towers. "
            "Same SIM observed across 3 different IMEIs.",
            "SUSPECT_MOVEMENT",
            base_dt_001,
            base_dt_001 + timedelta(hours=6)
        )

        ev1 = await generate_suspect_movement(conn, ctx, case1_id, base_dt_001,
                                               n_phones=t1_phones, pings_per_phone=t1_pings)
        ev2 = await generate_sim_imei_reuse(conn, ctx, case1_id,
                                             base_dt_001 + timedelta(hours=1),
                                             n_devices=t1_sims, pings_per_device=t1_sim_pings)
        print(f"  -> {ev1 + ev2} events generated for BENCH-TELECOM-001")

        # ── BENCH-TELECOM-002: COMMON_TOWER_OVERLAP + CROSS_CASE_LINK ──
        print("\n[PHASE 3] Creating BENCH-TELECOM-002...")
        base_dt_002 = datetime(2026, 3, 14, 18, 0, 0, tzinfo=timezone.utc)
        overlap_tower = next(t for t in ctx_towers if t["code"] == "TOWER-RH-01")

        # Save some phones/devices from case 1 to share into case 2
        shared_phone_ids = list(ctx.phones.values())[:3]
        shared_device_ids = list(ctx.devices.values())[:2]

        case2_id = await create_benchmark_case(
            conn, run_id,
            "BENCH-TELECOM-002",
            "Rohini Co-location & Cross-Case Suspect Network",
            "Synthetic scenario: 5 phones converge at Rohini Sector 3 tower. "
            "3 phones also appeared in BENCH-TELECOM-001.",
            "COMMON_TOWER_OVERLAP",
            base_dt_002,
            base_dt_002 + timedelta(hours=4)
        )

        ev3 = await generate_co_location(conn, ctx, case2_id, base_dt_002,
                                          n_phones=t2_phones, overlap_tower=overlap_tower,
                                          total_pings=t2_pings)
        print(f"  -> {ev3} events generated for BENCH-TELECOM-002")

        # Register cross-case links
        await create_cross_case_links(conn, ctx, case1_id, case2_id,
                                       shared_phone_ids, shared_device_ids, run_id)
        print(f"  -> {len(shared_phone_ids)} cross-case phone links + {len(shared_device_ids)} device links registered")

    # ── Post-Generation Verification ──
    print("\n[VERIFICATION] Running post-generation checks...")
    async with engine.connect() as conn:
        await verify_database_identity(conn)
        primary_ok = await verify_primary_unchanged(conn, baseline_before)
        hero_ok_after = await verify_hero_unchanged(conn, hero)
        report = await produce_verification_report(conn, run_id, hero, baseline_before)

    await engine.dispose()

    # ── Print Report ──
    print("\n" + "=" * 60)
    print("CIVIX 2.0 TELECOM BENCHMARK — GENERATION REPORT")
    print("=" * 60)
    print(f"Generation Run ID      : {run_id}")
    print(f"Generator Version      : {GENERATOR_VERSION}")
    print(f"Seed                   : {DETERMINISTIC_SEED}")
    print()
    print("── PRIMARY CIVIX WORLD ─────────────────────────────────")
    verdict = "UNCHANGED [OK]" if not report['primary_civix_changed'] else "[!] CHANGED — INVESTIGATE IMMEDIATELY"
    print(f"  Primary CIVIX schema : {verdict}")
    print(f"  Hero cases expected  : {report['hero_count_expected']}")
    hero_verdict = "INTACT [OK]" if report['hero_intact'] else "[!] MISSING — HARD FAIL"
    print(f"  Hero cases status    : {hero_verdict}")
    print()
    print("── BENCHMARK SCHEMA ────────────────────────────────────")
    print(f"  Cases                : {report['benchmark_benchmark_case_count']}")
    print(f"  Events               : {report['benchmark_benchmark_event_count']}")
    print(f"  Towers               : {report['benchmark_benchmark_tower_count']}")
    print(f"  Phones               : {report['benchmark_benchmark_phone_count']}")
    print(f"  Devices              : {report['benchmark_benchmark_device_count']}")
    print(f"  SIMs                 : {report['benchmark_benchmark_sim_count']}")
    print(f"  SIM-Device Links     : {report['benchmark_benchmark_sim_device_link_count']}")
    print(f"  Cross-Case Links     : {report['benchmark_benchmark_cross_case_link_count']}")
    print()
    print("── DATA INTEGRITY ──────────────────────────────────────")
    print(f"  Provenance violations: {report['benchmark_provenance_violations']}")
    print(f"  Synthetic flag viol. : {report['benchmark_synthetic_flag_violations']}")
    print()

    if (not report['primary_civix_changed'] and
            report['hero_intact'] and
            report['benchmark_provenance_violations'] == 0 and
            report['benchmark_synthetic_flag_violations'] == 0 and
            report['benchmark_benchmark_event_count'] > 0):
        print("RESULT: PRIMARY CIVIX WORLD UNCHANGED [OK]")
        print("RESULT: BENCHMARK GENERATION SUCCESSFUL [OK]")
    else:
        print("RESULT: VALIDATION FAILED — REVIEW REPORT ABOVE")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CIVIX Telecom Benchmark Generator")
    parser.add_argument("--tier", type=int, default=1, choices=[1, 2], help="Generation tier density")
    args = parser.parse_args()
    
    asyncio.run(run_generation(tier=args.tier))


"""
Phase 7.5 — Analytical Read-Only Queries
READ-ONLY. No inserts, updates, or deletes.
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import dotenv_values

env = dotenv_values('.env')
engine = create_async_engine(env['CIVIX_DATABASE_URL'])


async def section(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


async def run():
    async with engine.connect() as conn:

        # ─── SECTION 1: State Verification ───────────────────────────
        await section("SECTION 1: DATABASE IDENTITY")
        r = await conn.execute(text("SELECT current_database()"))
        db = r.scalar()
        print("Database:", db)
        assert db == "civix_demo", f"SAFETY STOP: Unexpected database: {db}"

        await section("SECTION 2: BENCHMARK COUNTS")
        tables = [
            ("benchmark_case", "civix_telecom_benchmark"),
            ("benchmark_event", "civix_telecom_benchmark"),
            ("benchmark_tower", "civix_telecom_benchmark"),
            ("benchmark_phone", "civix_telecom_benchmark"),
            ("benchmark_device", "civix_telecom_benchmark"),
            ("benchmark_sim", "civix_telecom_benchmark"),
            ("benchmark_sim_device_link", "civix_telecom_benchmark"),
            ("benchmark_cross_case_link", "civix_telecom_benchmark"),
        ]
        for tbl, schema in tables:
            r = await conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{tbl}"))
            print(f"  {tbl}: {r.scalar()}")

        r = await conn.execute(text("""
            SELECT generation_run_id::text, tier, seed, generator_version, notes, created_at
            FROM civix_telecom_benchmark.generation_run
            ORDER BY created_at DESC LIMIT 5
        """))
        print("\nGeneration Runs (latest first):")
        for row in r.fetchall():
            m = row._mapping
            run_id = str(m["generation_run_id"])
            print(f"  run_id={run_id} tier={m['tier']} seed={m['seed']} notes={m['notes']}")

        await section("SECTION 3: PRIMARY CIVIX COUNTS")
        primary_tables = [
            ("investigative_case", "civix"),
            ("event", "civix"),
            ("event_participant", "civix"),
            ("entity", "civix"),
            ("phone_number", "civix"),
            ("sim", "civix"),
            ("device", "civix"),
        ]
        expected = {
            "investigative_case": 267,
            "event": 2201,
            "event_participant": 2251,
            "entity": 60796,
            "phone_number": 15026,
            "sim": 15000,
            "device": 7525,
        }
        for tbl, schema in primary_tables:
            r = await conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{tbl}"))
            actual = r.scalar()
            exp = expected.get(tbl, "?")
            status = "OK" if actual == exp else f"MISMATCH! Expected {exp}"
            print(f"  {tbl}: {actual}  [{status}]")

        # ─── SECTION 4: BENCH-002 Event Inventory ─────────────────────
        await section("SECTION 4: BENCH-TELECOM-002 EVENT INVENTORY")

        r = await conn.execute(text("""
            SELECT bc.id::text, bc.case_number, bc.scenario_type
            FROM civix_telecom_benchmark.benchmark_case bc
            WHERE bc.case_number IN ('BENCH-TELECOM-001', 'BENCH-TELECOM-002')
            ORDER BY bc.case_number
        """))
        cases = {row._mapping["case_number"]: row._mapping["id"] for row in r.fetchall()}
        print("Cases found:", list(cases.keys()))

        case2_id = cases.get("BENCH-TELECOM-002")
        if not case2_id:
            print("ERROR: BENCH-TELECOM-002 not found!")
            return

        # Events by type
        r = await conn.execute(text("""
            SELECT event_type, COUNT(*) as cnt
            FROM civix_telecom_benchmark.benchmark_event
            WHERE case_id = :cid
            GROUP BY event_type ORDER BY cnt DESC
        """), {"cid": case2_id})
        print("\nEvents by type (BENCH-002):")
        for row in r.fetchall():
            m = row._mapping
            print(f"  {m['event_type']}: {m['cnt']}")

        # Events by tower
        r = await conn.execute(text("""
            SELECT bt.tower_code, bt.name, COUNT(be.id) as hit_count,
                   COUNT(DISTINCT be.caller_phone_id) as unique_callers,
                   COUNT(DISTINCT be.callee_phone_id) as unique_callees,
                   COUNT(DISTINCT be.subject_phone_id) as unique_subjects
            FROM civix_telecom_benchmark.benchmark_event be
            JOIN civix_telecom_benchmark.benchmark_tower bt ON be.tower_id = bt.id
            WHERE be.case_id = :cid
            GROUP BY bt.id, bt.tower_code, bt.name
            ORDER BY hit_count DESC
            LIMIT 10
        """), {"cid": case2_id})
        print("\nTop towers by event count (BENCH-002):")
        for row in r.fetchall():
            m = row._mapping
            print(f"  {m['tower_code']} ({m['name']}): {m['hit_count']} hits | callers={m['unique_callers']} callees={m['unique_callees']} subjects={m['unique_subjects']}")

        # Unique phones
        r = await conn.execute(text("""
            SELECT COUNT(DISTINCT phone_id) as unique_phones FROM (
                SELECT caller_phone_id as phone_id FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid AND caller_phone_id IS NOT NULL
                UNION
                SELECT callee_phone_id FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid AND callee_phone_id IS NOT NULL
                UNION
                SELECT subject_phone_id FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid AND subject_phone_id IS NOT NULL
            ) q
        """), {"cid": case2_id})
        print(f"\nUnique phones (BENCH-002): {r.scalar()}")

        r = await conn.execute(text("""
            SELECT COUNT(DISTINCT device_id) FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid AND device_id IS NOT NULL
        """), {"cid": case2_id})
        print(f"Unique devices (BENCH-002): {r.scalar()}")

        r = await conn.execute(text("""
            SELECT COUNT(DISTINCT sim_id) FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid AND sim_id IS NOT NULL
        """), {"cid": case2_id})
        print(f"Unique SIMs (BENCH-002): {r.scalar()}")

        # Temporal span
        r = await conn.execute(text("""
            SELECT MIN(occurred_at), MAX(occurred_at) FROM civix_telecom_benchmark.benchmark_event WHERE case_id = :cid
        """), {"cid": case2_id})
        row = r.fetchone()
        print(f"Temporal span (BENCH-002): {row[0]} -> {row[1]}")

        # Events per phone distribution
        r = await conn.execute(text("""
            SELECT phone_id, cnt FROM (
                SELECT caller_phone_id as phone_id, COUNT(*) as cnt
                FROM civix_telecom_benchmark.benchmark_event
                WHERE case_id = :cid AND caller_phone_id IS NOT NULL
                GROUP BY caller_phone_id
            ) q ORDER BY cnt DESC LIMIT 5
        """), {"cid": case2_id})
        print("\nTop 5 phones by caller event count (BENCH-002):")
        for row in r.fetchall():
            m = row._mapping
            print(f"  phone_id={str(m['phone_id'])[:8]}... events={m['cnt']}")

        # ─── SECTION 5: TOWER-SHARING ANALYSIS ────────────────────────
        await section("SECTION 5: TOWER-SHARING ANALYSIS (BENCH-002)")

        # For this we look at CALL events which have both caller and callee
        # and DEVICE_PING which have subject_phone
        # Co-location requires two DISTINCT phones on same tower near same time

        r = await conn.execute(text("""
            SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event
            WHERE case_id = :cid AND caller_phone_id IS NOT NULL AND callee_phone_id IS NOT NULL
        """), {"cid": case2_id})
        print(f"CALL events with both caller+callee: {r.scalar()}")

        r = await conn.execute(text("""
            SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event
            WHERE case_id = :cid AND event_type = 'DEVICE_PING'
        """), {"cid": case2_id})
        print(f"DEVICE_PING events: {r.scalar()}")

        # ─── SECTION 6: TEMPORAL OVERLAP ANALYSIS ─────────────────────
        await section("SECTION 6: TEMPORAL OVERLAP ANALYSIS - BENCHMARK APPROACH")

        # The API co-location endpoint requires msisdn_a and msisdn_b as explicit inputs.
        # This means it does NOT scan all phone pairs — it only evaluates a specific pair.
        # Let's measure what the aggregate tower-overlap picture looks like across ALL phone pairs.

        print("\nSame-tower CALL pairs (A and B parties of same CALL event = same tower by definition):")
        r = await conn.execute(text("""
            SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event
            WHERE case_id = :cid
              AND caller_phone_id IS NOT NULL
              AND callee_phone_id IS NOT NULL
              AND caller_phone_id != callee_phone_id
        """), {"cid": case2_id})
        same_tower_calls = r.scalar()
        print(f"  CALL events with distinct caller/callee (same tower implied): {same_tower_calls}")

        print("\nCross-event tower sharing (two events at same tower, different phones):")
        for window_label, window_secs in [("exact", 0), ("1min", 60), ("5min", 300), ("15min", 900), ("30min", 1800), ("60min", 3600)]:
            r = await conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT DISTINCT
                        LEAST(a.effective_phone, b.effective_phone) as pa,
                        GREATEST(a.effective_phone, b.effective_phone) as pb,
                        a.tower_id
                    FROM (
                        SELECT occurred_at, tower_id,
                               COALESCE(caller_phone_id, subject_phone_id) as effective_phone
                        FROM civix_telecom_benchmark.benchmark_event
                        WHERE case_id = :cid AND tower_id IS NOT NULL
                          AND COALESCE(caller_phone_id, subject_phone_id) IS NOT NULL
                    ) a
                    JOIN (
                        SELECT occurred_at, tower_id,
                               COALESCE(caller_phone_id, subject_phone_id) as effective_phone
                        FROM civix_telecom_benchmark.benchmark_event
                        WHERE case_id = :cid AND tower_id IS NOT NULL
                          AND COALESCE(caller_phone_id, subject_phone_id) IS NOT NULL
                    ) b ON a.tower_id = b.tower_id AND a.effective_phone != b.effective_phone
                       AND ABS(EXTRACT(EPOCH FROM (a.occurred_at - b.occurred_at))) <= :window
                ) q
            """), {"cid": case2_id, "window": window_secs})
            count = r.scalar()
            print(f"  Window ±{window_label}: {count} unique phone-pair/tower combinations")

        # ─── SECTION 7: CO-LOCATION ENDPOINT DISSECTION ────────────────
        await section("SECTION 7: CO-LOCATION ALGORITHM ANALYSIS")
        print("""
The endpoint GET /api/v1/telecom/co-location requires:
  - msisdn_a (required): First MSISDN
  - msisdn_b (required): Second MSISDN  
  - case_id (optional): For benchmark routing
  - overlap_window_seconds (default: 3600): Time threshold
  
DESIGN: It is a PAIRWISE lookup — NOT a scan of all phone pairs.
The caller must know which two phones to compare.
This is fundamentally different from a global co-location discovery query.

BENCHMARK ALGORITHM (from code inspection, lines 1283-1322):
  1. Fetch all events for msisdn_a in benchmark schema (caller OR callee OR subject)
  2. Fetch all events for msisdn_b in benchmark schema
  3. JOIN on same tower_id
  4. Filter: ABS(time_a - time_b) <= overlap_window_seconds
  5. No deduplication / no self-match filtering (but phones differ by param)
  6. Returns ALL matching (event_a, event_b, tower, gap) rows — not deduplicated by pair

CRITICAL ISSUE: No pagination on co-location results.
All matching rows are returned in one response. With 1,500 events each,
a shared phone pair could produce O(n*m) rows if they appear on same towers.
""")

        # Count actual events per phone in case 2
        # First get a sample of phones used in BENCH-002
        r = await conn.execute(text("""
            SELECT p.msisdn, COUNT(be.id) as event_count
            FROM civix_telecom_benchmark.benchmark_phone p
            JOIN civix_telecom_benchmark.benchmark_event be ON (
                be.caller_phone_id = p.id OR be.callee_phone_id = p.id OR be.subject_phone_id = p.id
            )
            WHERE be.case_id = :cid
            GROUP BY p.id, p.msisdn
            ORDER BY event_count DESC
            LIMIT 10
        """), {"cid": case2_id})
        print("\nTop 10 phones by event count in BENCH-002:")
        top_phones_002 = []
        for row in r.fetchall():
            m = row._mapping
            top_phones_002.append(m['msisdn'])
            print(f"  {m['msisdn']}: {m['event_count']} events")

        # ─── SECTION 8: CROSS-CASE CO-LOCATION ─────────────────────────
        await section("SECTION 8: CROSS-CASE LINK ANALYSIS")

        r = await conn.execute(text("""
            SELECT ccl.entity_type, ccl.entity_id::text,
                   ca.case_number as case_a, cb.case_number as case_b,
                   ccl.link_note
            FROM civix_telecom_benchmark.benchmark_cross_case_link ccl
            JOIN civix_telecom_benchmark.benchmark_case ca ON ccl.case_a_id = ca.id
            JOIN civix_telecom_benchmark.benchmark_case cb ON ccl.case_b_id = cb.id
        """))
        cross_links = r.fetchall()
        print(f"\nCross-case links: {len(cross_links)}")
        phone_cross_ids = []
        device_cross_ids = []
        for row in cross_links:
            m = row._mapping
            print(f"  type={m['entity_type']} entity={str(m['entity_id'])[:16]}... {m['case_a']} <-> {m['case_b']} note={m['link_note']}")
            if m['entity_type'] == 'PHONE':
                phone_cross_ids.append(m['entity_id'])
            elif m['entity_type'] == 'DEVICE':
                device_cross_ids.append(m['entity_id'])

        # Verify shared phone appears in both cases
        if phone_cross_ids:
            for pid in phone_cross_ids[:3]:
                r = await conn.execute(text("""
                    SELECT bc.case_number, COUNT(be.id) as events, bp.msisdn
                    FROM civix_telecom_benchmark.benchmark_event be
                    JOIN civix_telecom_benchmark.benchmark_case bc ON be.case_id = bc.id
                    JOIN civix_telecom_benchmark.benchmark_phone bp ON bp.id = :phone_id
                    WHERE (be.caller_phone_id = :phone_id OR be.callee_phone_id = :phone_id OR be.subject_phone_id = :phone_id)
                    GROUP BY bc.case_number, bp.msisdn
                """), {"phone_id": pid})
                rows_data = r.fetchall()
                if rows_data:
                    msisdn = rows_data[0]._mapping['msisdn']
                    print(f"\n  Shared phone {msisdn}:")
                    for row in rows_data:
                        m = row._mapping
                        print(f"    case={m['case_number']}: {m['events']} events")

        # ─── SECTION 9: DUPLICATE/SELF-MATCH AUDIT ─────────────────────
        await section("SECTION 9: DUPLICATE/SELF-MATCH AUDIT")

        # The co-location endpoint takes msisdn_a and msisdn_b as params.
        # Self-match is prevented by caller specifying different MSISDNs.
        # But what happens if same phone appears as both caller and callee in an event?
        r = await conn.execute(text("""
            SELECT COUNT(*) FROM civix_telecom_benchmark.benchmark_event
            WHERE case_id = :cid AND caller_phone_id = callee_phone_id
        """), {"cid": case2_id})
        print(f"Self-call events (caller=callee): {r.scalar()}")

        # Check if A->B and B->A both generate rows (symmetric duplicates in result)
        print("""
NOTE: The co-location endpoint does NOT deduplicate symmetric pairs.
If phone A appears at tower X at T=0 and phone B appears at tower X at T=30s,
the query returns: (event_a, event_b, gap=30) AND (event_b, event_a, gap=30)
if msisdn_a=A, msisdn_b=B. Only one call is made per pair direction, so
symmetric duplication within a single API call is: 
  each event of A paired with each event of B on same tower within window.
This is the Cartesian product of A's events x B's events on same towers.
""")

        # ─── SECTION 10: EXPECTED CO-LOCATION RESULTS ──────────────────
        await section("SECTION 10: EXPECTED CO-LOCATION RESULTS ANALYSIS")

        # Let's pick two phones from BENCH-002 and simulate what co-location would return
        if len(top_phones_002) >= 2:
            phone_a = top_phones_002[0]
            phone_b = top_phones_002[1]

            r = await conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT a.id as event_a, b.id as event_b, a.tower_id, a.occurred_at as ta, b.occurred_at as tb
                    FROM civix_telecom_benchmark.benchmark_event a
                    JOIN civix_telecom_benchmark.benchmark_phone pa ON (a.caller_phone_id = pa.id OR a.callee_phone_id = pa.id OR a.subject_phone_id = pa.id)
                    JOIN civix_telecom_benchmark.benchmark_event b ON a.tower_id = b.tower_id
                    JOIN civix_telecom_benchmark.benchmark_phone pb ON (b.caller_phone_id = pb.id OR b.callee_phone_id = pb.id OR b.subject_phone_id = pb.id)
                    WHERE a.case_id = :cid AND b.case_id = :cid
                      AND pa.msisdn = :pa AND pb.msisdn = :pb
                      AND ABS(EXTRACT(EPOCH FROM (a.occurred_at - b.occurred_at))) <= 3600
                ) q
            """), {"cid": case2_id, "pa": phone_a, "pb": phone_b})
            count = r.scalar()
            print(f"Co-location pairs for {phone_a} vs {phone_b} (window=3600s): {count} raw rows")

            r = await conn.execute(text("""
                SELECT COUNT(DISTINCT tower_id) FROM (
                    SELECT a.tower_id
                    FROM civix_telecom_benchmark.benchmark_event a
                    JOIN civix_telecom_benchmark.benchmark_phone pa ON (a.caller_phone_id = pa.id OR a.callee_phone_id = pa.id OR a.subject_phone_id = pa.id)
                    JOIN civix_telecom_benchmark.benchmark_event b ON a.tower_id = b.tower_id
                    JOIN civix_telecom_benchmark.benchmark_phone pb ON (b.caller_phone_id = pb.id OR b.callee_phone_id = pb.id OR b.subject_phone_id = pb.id)
                    WHERE a.case_id = :cid AND b.case_id = :cid
                      AND pa.msisdn = :pa AND pb.msisdn = :pb
                      AND ABS(EXTRACT(EPOCH FROM (a.occurred_at - b.occurred_at))) <= 3600
                ) q
            """), {"cid": case2_id, "pa": phone_a, "pb": phone_b})
            print(f"  Distinct towers shared: {r.scalar()}")

        # ─── SECTION 11: RESPONSE SIZE ANALYSIS ────────────────────────
        await section("SECTION 11: RESPONSE SIZE ANALYSIS")
        print("""
Previous co-location test result: ~394 KB / ~441ms.

The co-location endpoint returns ALL rows without pagination.
Each row contains: tower_id, tower_name, msisdn_a, msisdn_b, time_a, time_b, gap_seconds, supporting_event_ids (2), confidence, note.
That is approximately 10 fields per row.

At ~394 KB for the response with 0 items returned, this is SERIALIZATION OVERHEAD
from the response envelope and data quality metadata.

If co_locations_found was 0, the 394 KB is suspicious.
Let's check whether the phones used in the prior test were actually related.
""")

        # ─── SECTION 12: PRIMARY INTEGRITY RECHECK ─────────────────────
        await section("SECTION 12: PRIMARY INTEGRITY FINAL CHECK")

        # Check no benchmark data in civix schema
        r = await conn.execute(text("""
            SELECT COUNT(*) FROM civix.investigative_case
            WHERE case_number LIKE 'BENCH-%'
        """))
        bench_in_primary = r.scalar()
        print(f"BENCH- cases in civix.investigative_case: {bench_in_primary} (expected 0)")

        r = await conn.execute(text("SELECT COUNT(*) FROM civix.outbox WHERE payload::text LIKE '%BENCH%'"))
        print(f"Outbox entries with BENCH: {r.scalar()} (expected 0)")

        # Confirm no cross-schema FKs
        r = await conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.referential_constraints rc
            JOIN information_schema.key_column_usage kcu ON rc.constraint_name = kcu.constraint_name
            WHERE kcu.table_schema = 'civix_telecom_benchmark'
              AND rc.unique_constraint_schema = 'civix'
        """))
        cross_schema_fks = r.scalar()
        print(f"Cross-schema FKs (benchmark -> civix): {cross_schema_fks} (expected 0)")

        print("\nDone.")

asyncio.run(run())

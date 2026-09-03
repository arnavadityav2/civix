"""
C4 Remediation Diagnostic Scripts
Run these to gather facts for all 10 remediation requirements.
"""
import asyncio
import asyncpg
import json
import hashlib
import sys

DB_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"
CASE_ID = "b281ad86-1b43-458c-b751-fc44cb467823"
VIKRAM_ID = "fb123ba2-737a-4d12-ad72-93a3bf9efcd3"
NEHA_ID   = "14fb86ef-06a7-4544-9c54-844821fff38b"


async def run():
    conn = await asyncpg.connect(DB_DSN)

    print("=" * 70)
    print("DIAGNOSTIC 1: VIKRAM ↔ NEHA DIRECT ASSERTIONS")
    print("=" * 70)

    rows = await conn.fetch("""
        SELECT
            a.assertion_id,
            a.predicate,
            a.subject_entity_id,
            a.object_entity_id,
            a.epistemic_status,
            se.entity_type AS subj_type,
            oe.entity_type AS obj_type,
            sp.display_name AS subj_name,
            op.display_name AS obj_name
        FROM civix.assertion a
        JOIN civix.entity se ON se.entity_id = a.subject_entity_id
        JOIN civix.entity oe ON oe.entity_id = a.object_entity_id
        LEFT JOIN civix.person sp ON sp.entity_id = a.subject_entity_id
        LEFT JOIN civix.person op ON op.entity_id = a.object_entity_id
        WHERE (
            (a.subject_entity_id = $1 AND a.object_entity_id = $2)
            OR
            (a.subject_entity_id = $2 AND a.object_entity_id = $1)
        )
    """, VIKRAM_ID, NEHA_ID)

    if not rows:
        print("NO DIRECT ASSERTIONS between Vikram and Neha.")
        print("=> Relationship must be indirect (multi-hop)")
    else:
        for r in rows:
            print(f"  DIRECT ASSERTION FOUND!")
            print(f"  assertion_id: {r['assertion_id']}")
            print(f"  predicate: {r['predicate']}")
            print(f"  subject: {r['subj_name']} ({r['subject_entity_id']}) [{r['subj_type']}]")
            print(f"  object:  {r['obj_name']} ({r['object_entity_id']}) [{r['obj_type']}]")
            print(f"  epistemic_status: {r['epistemic_status']}")
            print()

    print("=" * 70)
    print("DIAGNOSTIC 2: ALL ASSERTIONS WHERE VIKRAM IS SUBJECT")
    print("=" * 70)
    rows2 = await conn.fetch("""
        SELECT
            a.assertion_id, a.predicate,
            a.object_entity_id,
            oe.entity_type AS obj_type,
            COALESCE(op.display_name, org.legal_name, v.make, l.location_name, 'UNKNOWN') AS obj_name,
            a.epistemic_status,
            a.authorized_case_ids
        FROM civix.assertion a
        JOIN civix.entity oe ON oe.entity_id = a.object_entity_id
        LEFT JOIN civix.person op ON op.entity_id = a.object_entity_id
        LEFT JOIN civix.organization org ON org.entity_id = a.object_entity_id
        LEFT JOIN civix.vehicle v ON v.entity_id = a.object_entity_id
        LEFT JOIN civix.location l ON l.entity_id = a.object_entity_id
        WHERE a.subject_entity_id = $1
    """, VIKRAM_ID)

    for r in rows2:
        print(f"  {r['predicate']} -> {r['obj_name']} ({r['object_entity_id']}) [{r['obj_type']}]  epi={r['epistemic_status']}  cases={r['authorized_case_ids']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 3: ALL ASSERTIONS WHERE NEHA IS SUBJECT OR OBJECT (non-Vikram)")
    print("=" * 70)
    rows3 = await conn.fetch("""
        SELECT
            a.assertion_id, a.predicate,
            a.subject_entity_id, a.object_entity_id,
            se.entity_type AS subj_type,
            oe.entity_type AS obj_type,
            COALESCE(sp.display_name, 'UNKNOWN') AS subj_name,
            COALESCE(op.display_name, org.legal_name, v.make, l.location_name, 'UNKNOWN') AS obj_name,
            a.epistemic_status
        FROM civix.assertion a
        JOIN civix.entity se ON se.entity_id = a.subject_entity_id
        JOIN civix.entity oe ON oe.entity_id = a.object_entity_id
        LEFT JOIN civix.person sp ON sp.entity_id = a.subject_entity_id
        LEFT JOIN civix.person op ON op.entity_id = a.object_entity_id
        LEFT JOIN civix.organization org ON org.entity_id = a.object_entity_id
        LEFT JOIN civix.vehicle v ON v.entity_id = a.object_entity_id
        LEFT JOIN civix.location l ON l.entity_id = a.object_entity_id
        WHERE (a.subject_entity_id = $1 OR a.object_entity_id = $1)
          AND a.subject_entity_id != $2 AND a.object_entity_id != $2
    """, NEHA_ID, VIKRAM_ID)

    for r in rows3:
        print(f"  {r['subj_name']} --[{r['predicate']}]--> {r['obj_name']} ({r['object_entity_id']}) [{r['obj_type']}]  epi={r['epistemic_status']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 4: SHARED EVENTS (Vikram + Neha at same event)")
    print("=" * 70)
    rows4 = await conn.fetch("""
        SELECT
            e.event_id, e.event_type, lower(e.occurred_at) AS event_time,
            ep1.participant_role AS vikram_role,
            ep2.participant_role AS neha_role
        FROM civix.event e
        JOIN civix.event_participant ep1 ON ep1.event_id = e.event_id AND ep1.entity_id = $1
        JOIN civix.event_participant ep2 ON ep2.event_id = e.event_id AND ep2.entity_id = $2
    """, VIKRAM_ID, NEHA_ID)

    if not rows4:
        print("  No shared events found between Vikram and Neha")
    else:
        for r in rows4:
            print(f"  event_id={r['event_id']} type={r['event_type']} time={r['event_time']}")
            print(f"    vikram_role={r['vikram_role']}  neha_role={r['neha_role']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 5: MULTI-HOP - Vikram's common contacts with Neha")
    print("(Find person P such that Vikram→P assertion AND Neha→P assertion)")
    print("=" * 70)
    rows5 = await conn.fetch("""
        SELECT
            a1.predicate AS v_pred, a2.predicate AS n_pred,
            a1.object_entity_id AS common_entity_id,
            oe.entity_type AS common_type,
            COALESCE(op.display_name, org.legal_name, 'UNKNOWN') AS common_name
        FROM civix.assertion a1
        JOIN civix.assertion a2 ON a1.object_entity_id = a2.object_entity_id
        JOIN civix.entity oe ON oe.entity_id = a1.object_entity_id
        LEFT JOIN civix.person op ON op.entity_id = a1.object_entity_id
        LEFT JOIN civix.organization org ON org.entity_id = a1.object_entity_id
        WHERE a1.subject_entity_id = $1
          AND a2.subject_entity_id = $2
    """, VIKRAM_ID, NEHA_ID)

    if not rows5:
        print("  No shared assertion targets found")
    else:
        for r in rows5:
            print(f"  Common: {r['common_name']} ({r['common_entity_id']}) [{r['common_type']}]")
            print(f"    Vikram --[{r['v_pred']}]--> Common")
            print(f"    Neha   --[{r['n_pred']}]--> Common")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 6: EXISTING INVESTIGATIVE FINDINGS for Neha in this case")
    print("=" * 70)
    rows6 = await conn.fetch("""
        SELECT
            f.finding_id, f.finding_type, f.subject_entity_id, f.object_entity_id,
            f.relationship_strength, f.hop_count, f.path_description,
            f.key_facts, f.evidence_ids, f.suppressed
        FROM civix.investigative_finding f
        JOIN civix.investigative_lead l ON l.lead_id = f.lead_id
        WHERE l.case_id = $1 AND l.target_entity_id = $2
    """, CASE_ID, NEHA_ID)

    if not rows6:
        print("  No findings for Neha's lead in this case yet")
    else:
        for r in rows6:
            print(f"  finding_type={r['finding_type']} hop_count={r['hop_count']} suppressed={r['suppressed']}")
            print(f"    subject={r['subject_entity_id']}  object={r['object_entity_id']}")
            print(f"    path={r['path_description']}")
            print(f"    key_facts={r['key_facts']}")
            print(f"    evidence_ids={r['evidence_ids']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 7: NEHA ↔ Horizon Logistics vs Global Exports (ground truth drift check)")
    print("=" * 70)
    org_rows = await conn.fetch("""
        SELECT o.entity_id, o.legal_name
        FROM civix.organization o
        WHERE o.legal_name ILIKE '%horizon%' OR o.legal_name ILIKE '%global%'
    """)
    for r in org_rows:
        print(f"  org: {r['legal_name']} ({r['entity_id']})")

    horizon_rows = await conn.fetch("""
        SELECT a.assertion_id, a.predicate, a.subject_entity_id, a.object_entity_id, a.epistemic_status
        FROM civix.assertion a
        JOIN civix.organization o ON o.entity_id = a.object_entity_id
        WHERE a.subject_entity_id = $1
          AND (o.legal_name ILIKE '%horizon%' OR o.legal_name ILIKE '%global%')
    """, NEHA_ID)
    for r in horizon_rows:
        print(f"  Neha assertion: {r['predicate']} -> {r['object_entity_id']}  epi={r['epistemic_status']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 8: Vikram ↔ Global Exports assertion")
    print("=" * 70)
    global_rows = await conn.fetch("""
        SELECT a.assertion_id, a.predicate, a.object_entity_id, o.legal_name, a.epistemic_status
        FROM civix.assertion a
        JOIN civix.organization o ON o.entity_id = a.object_entity_id
        WHERE a.subject_entity_id = $1
          AND o.legal_name ILIKE '%global%'
    """, VIKRAM_ID)
    for r in global_rows:
        print(f"  Vikram -> {r['legal_name']} via [{r['predicate']}]  epi={r['epistemic_status']}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 9: FEATURE VECTOR SCHEMA (EXPECTED_FEATURES count)")
    print("=" * 70)
    # We pull from the code itself
    EXPECTED_FEATURES = [
        "total_calls", "active_days", "unique_contacts", "unique_cell_sectors",
        "voice_calls", "sms_count", "data_sessions", "median_duration_sec",
        "short_call_ratio", "night_call_count", "night_call_ratio", "weekend_call_ratio",
        "calls_per_active_day", "contact_concentration", "unique_counterparties",
        "txn_type_diversity", "total_sent_amount", "avg_txn_amount", "median_txn_amount",
        "max_txn_amount", "min_txn_amount", "std_txn_amount", "high_value_txn_count",
        "high_value_txn_ratio", "amount_concentration", "unique_sectors", "unique_regions",
        "geo_spread_degrees", "lat_stddev", "lon_stddev", "location_active_days",
        "cross_region_ratio", "active_day_delta", "calls_per_txn", "call_duration_cv",
        "txn_amount_cv", "comm_span_days", "txn_span_days", "dual_concentration",
        "total_network_size", "gender_MALE", "gender_OTHER",
        "occupation_Businessman", "occupation_Carpenter", "occupation_Contractor",
        "occupation_Doctor", "occupation_Driver", "occupation_Electrician",
        "occupation_Engineer", "occupation_Farmer", "occupation_Government Employee",
        "occupation_Hawker", "occupation_Housewife", "occupation_Laborer",
        "occupation_Mechanic", "occupation_Police Officer", "occupation_Shopkeeper",
        "occupation_Student", "occupation_Tailor", "occupation_Teacher",
        "occupation_Trader", "home_region_alwar", "home_region_bharatpur",
        "home_region_bikaner", "home_region_jaipur", "home_region_jodhpur",
        "home_region_kota", "home_region_pali", "home_region_sikar", "home_region_udaipur"
    ]
    print(f"  EXPECTED_FEATURES count: {len(EXPECTED_FEATURES)}")
    for i, f in enumerate(EXPECTED_FEATURES):
        print(f"  [{i:02d}] {f}")

    print()
    print("=" * 70)
    print("DIAGNOSTIC 10: VIKRAM ↔ RAHUL assertions (should be zero)")
    print("=" * 70)
    rahul_rows = await conn.fetch("""
        SELECT p.entity_id, p.display_name FROM civix.person p
        WHERE p.display_name ILIKE '%rahul%'
    """)
    for rr in rahul_rows:
        print(f"  Person: {rr['display_name']} ({rr['entity_id']})")
        assert_rows = await conn.fetch("""
            SELECT a.assertion_id, a.predicate FROM civix.assertion a
            WHERE (a.subject_entity_id = $1 AND a.object_entity_id = $2)
               OR (a.subject_entity_id = $2 AND a.object_entity_id = $1)
        """, VIKRAM_ID, rr['entity_id'])
        print(f"    Direct assertions with Vikram: {len(assert_rows)}")

    await conn.close()
    print()
    print("DONE.")


if __name__ == "__main__":
    asyncio.run(run())

import psycopg2

def cleanup_11d_contamination():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    print("==========================================================================")
    print("  GATE 11D-R1: DATABASE CONTAMINATION CLEANUP")
    print("==========================================================================")

    # 1. Identify exact contaminated location entity IDs
    cur.execute("SELECT entity_id, location_name FROM civix.location WHERE location_name = 'Test Loc';")
    bad_loc_rows = cur.fetchall()
    bad_loc_ids = [r[0] for r in bad_loc_rows]

    print(f"1. Identified {len(bad_loc_ids)} contaminated 'Test Loc' location rows:")
    for b_id, b_name in bad_loc_rows:
        print(f"   - Entity ID: {b_id} | Name: {b_name}")

    # 2. Identify exact contaminated event_location IDs
    cur.execute("""
        SELECT el.event_location_id, el.event_id, el.case_id, el.location_id
        FROM civix.event_location el
        WHERE el.location_id IN %s OR el.case_id = '7894c954-89c3-968b-1aad-71ff2fc8c62c';
    """, (tuple(bad_loc_ids),))
    bad_el_rows = cur.fetchall()
    bad_el_ids = [r[0] for r in bad_el_rows]
    bad_ev_ids = [r[1] for r in bad_el_rows]

    print(f"\n2. Identified {len(bad_el_ids)} contaminated event_location rows:")
    for el_id, ev_id, c_id, loc_id in bad_el_rows:
        print(f"   - EventLocation ID: {el_id} | Event ID: {ev_id} | Case ID: {c_id} | Loc ID: {loc_id}")

    # Safety Assertions before deletion
    assert len(bad_loc_ids) == 4, f"Expected exactly 4 Test Loc records, found {len(bad_loc_ids)}"
    assert len(bad_el_ids) == 4, f"Expected exactly 4 contaminated event_location records, found {len(bad_el_ids)}"

    # Perform Deletion / Tombstoning
    cur.execute("DELETE FROM civix.event_location WHERE event_location_id IN %s;", (tuple(bad_el_ids),))
    print(f"\n3. Deleted {cur.rowcount} contaminated event_location records.")

    cur.execute("DELETE FROM civix.event WHERE event_id IN %s;", (tuple(bad_ev_ids),))
    print(f"4. Deleted {cur.rowcount} contaminated event records.")

    cur.execute("DELETE FROM civix.location WHERE entity_id IN %s;", (tuple(bad_loc_ids),))
    print(f"5. Deleted {cur.rowcount} contaminated location records.")

    # ADR-018: civix.entity cannot be physically deleted; mark as TOMBSTONED
    cur.execute("UPDATE civix.entity SET visibility_status = 'TOMBSTONED' WHERE entity_id IN %s;", (tuple(bad_loc_ids),))
    print(f"6. Tombstoned {cur.rowcount} contaminated entity records (ADR-018).")

    conn.commit()

    # Post-Cleanup Verification
    cur.execute("SELECT count(*) FROM civix.location WHERE location_name = 'Test Loc';")
    rem_test_loc = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.location;")
    tot_loc = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.event_location;")
    tot_el = cur.fetchone()[0]

    print("\n==========================================================================")
    print("  POST-CLEANUP RECONCILIATION")
    print("==========================================================================")
    print(f"  - Contaminated 'Test Loc' Records Remaining : {rem_test_loc} (Expected 0)")
    print(f"  - Total civix.location Rows                : {tot_loc} (Expected 120: 100 synthetic + 20 NCR)")
    print(f"  - Total civix.event_location Rows          : {tot_el} (Expected 25)")
    print("==========================================================================")

    assert rem_test_loc == 0
    assert tot_loc == 120
    assert tot_el == 25

    # Run Ground Truth Oracle
    import subprocess
    oracle_res = subprocess.run(["python", "scripts/verify_pg_oracle.py"], capture_output=True, text=True)
    oracle_pass = "Verification Complete" in oracle_res.stdout
    print(f"  - Ground Truth Oracle Status               : {oracle_pass} (0 regressions)")
    assert oracle_pass

    conn.close()

if __name__ == "__main__":
    cleanup_11d_contamination()

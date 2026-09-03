import psycopg2
import json
import numpy as np

def run_phase11a_audit():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    audit = {}

    # 1. Quantities
    cur.execute("SELECT count(*) FROM civix.investigative_case;")
    audit["total_cases"] = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.event;")
    audit["total_events"] = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.location;")
    audit["total_locations"] = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM civix.location WHERE geometry IS NOT NULL AND ST_X(geometry) IS NOT NULL;")
    audit["locations_valid_geom"] = cur.fetchone()[0]
    audit["locations_missing_geom"] = audit["total_locations"] - audit["locations_valid_geom"]

    # Unique locations used by events via event_participant
    cur.execute("""
        SELECT count(DISTINCT ep.entity_id) 
        FROM civix.event_participant ep
        JOIN civix.location l ON l.entity_id = ep.entity_id;
    """)
    audit["unique_locs_in_events"] = cur.fetchone()[0]

    # Unique locations used by cases via case_entity_role -> event_participant -> location
    cur.execute("""
        SELECT count(DISTINCT ep.entity_id) 
        FROM civix.case_entity_role cer
        JOIN civix.event_participant ep_entity ON ep_entity.entity_id = cer.entity_id
        JOIN civix.event_participant ep ON ep.event_id = ep_entity.event_id
        JOIN civix.location l ON l.entity_id = ep.entity_id;
    """)
    audit["unique_locs_in_cases"] = cur.fetchone()[0]

    # Events linked to location vs unlinked
    cur.execute("""
        SELECT count(DISTINCT e.event_id)
        FROM civix.event e
        JOIN civix.event_participant ep ON ep.event_id = e.event_id
        JOIN civix.location l ON l.entity_id = ep.entity_id;
    """)
    audit["events_linked_loc"] = cur.fetchone()[0]
    audit["events_unlinked_loc"] = audit["total_events"] - audit["events_linked_loc"]

    # Timestamps
    cur.execute("SELECT count(*) FROM civix.event WHERE occurred_at IS NOT NULL;")
    audit["events_with_ts"] = cur.fetchone()[0]
    audit["events_missing_ts"] = audit["total_events"] - audit["events_with_ts"]

    # Case-level spatial statistics
    cur.execute("""
        SELECT 
            c.case_id::TEXT,
            c.case_number,
            c.title,
            COUNT(DISTINCT e.event_id) AS total_events,
            COUNT(DISTINCT CASE WHEN ep_loc.entity_id IS NOT NULL THEN e.event_id END) AS spatial_events,
            COUNT(DISTINCT ep_loc.entity_id) AS location_count
        FROM civix.investigative_case c
        LEFT JOIN civix.case_entity_role cer ON cer.case_id = c.case_id
        LEFT JOIN civix.event_participant ep_entity ON ep_entity.entity_id = cer.entity_id
        LEFT JOIN civix.event e ON e.event_id = ep_entity.event_id
        LEFT JOIN civix.event_participant ep_loc ON ep_loc.event_id = e.event_id AND ep_loc.entity_id IN (SELECT entity_id FROM civix.location)
        GROUP BY c.case_id, c.case_number, c.title;
    """)
    case_rows = cur.fetchall()

    tot_ev_list = [r[3] for r in case_rows]
    spat_ev_list = [r[4] for r in case_rows]
    loc_cnt_list = [r[5] for r in case_rows]

    audit["cases_with_ge_1_loc"] = sum(1 for r in case_rows if r[5] >= 1)
    audit["cases_with_0_loc"] = sum(1 for r in case_rows if r[5] == 0)

    audit["events_per_case"] = {
        "min": int(np.min(tot_ev_list)),
        "max": int(np.max(tot_ev_list)),
        "avg": float(np.mean(tot_ev_list)),
        "median": float(np.median(tot_ev_list))
    }

    audit["spatial_events_per_case"] = {
        "min": int(np.min(spat_ev_list)),
        "max": int(np.max(spat_ev_list)),
        "avg": float(np.mean(spat_ev_list)),
        "median": float(np.median(spat_ev_list))
    }

    audit["locs_per_case"] = {
        "min": int(np.min(loc_cnt_list)),
        "max": int(np.max(loc_cnt_list)),
        "avg": float(np.mean(loc_cnt_list)),
        "median": float(np.median(loc_cnt_list))
    }

    # Event types breakdown
    cur.execute("SELECT event_type, count(*) FROM civix.event GROUP BY event_type ORDER BY count DESC;")
    audit["event_type_counts"] = dict(cur.fetchall())

    cur.execute("""
        SELECT e.event_type, count(DISTINCT e.event_id)
        FROM civix.event e
        JOIN civix.event_participant ep ON ep.event_id = e.event_id
        JOIN civix.location l ON l.entity_id = ep.entity_id
        GROUP BY e.event_type;
    """)
    audit["event_types_spatial"] = dict(cur.fetchall())

    # Date range of spatial events
    cur.execute("""
        SELECT MIN(lower(e.occurred_at)), MAX(upper(e.occurred_at))
        FROM civix.event e
        JOIN civix.event_participant ep ON ep.event_id = e.event_id
        JOIN civix.location l ON l.entity_id = ep.entity_id;
    """)
    min_t, max_t = cur.fetchone()
    audit["spatial_event_min_time"] = str(min_t) if min_t else "N/A"
    audit["spatial_event_max_time"] = str(max_t) if max_t else "N/A"

    # Spatial bounding box of location points
    cur.execute("""
        SELECT MIN(ST_Y(geometry)), MAX(ST_Y(geometry)), MIN(ST_X(geometry)), MAX(ST_X(geometry))
        FROM civix.location
        WHERE geometry IS NOT NULL;
    """)
    min_lat, max_lat, min_lon, max_lon = cur.fetchone()
    audit["bbox"] = {
        "min_lat": float(min_lat) if min_lat else 0,
        "max_lat": float(max_lat) if max_lat else 0,
        "min_lon": float(min_lon) if min_lon else 0,
        "max_lon": float(max_lon) if max_lon else 0,
    }

    # Hero Cases audit
    hero_case_numbers = [
        "CASE-2026-0142", "CASE-2026-0187", "CASE-2026-0221", "CASE-2026-0042",
        "CASE-2026-0099", "CASE-2026-0112", "CASE-2026-0155", "CASE-2026-0201",
        "CASE-2026-0210", "CASE-2026-0234", "CASE-2026-0240", "CASE-2026-0248"
    ]
    cur.execute("""
        SELECT 
            c.case_id::TEXT, c.case_number, c.title, c.case_type, c.priority,
            COUNT(DISTINCT cer.entity_id) AS entity_count
        FROM civix.investigative_case c
        LEFT JOIN civix.case_entity_role cer ON cer.case_id = c.case_id
        WHERE c.case_number = ANY(%s)
        GROUP BY c.case_id, c.case_number, c.title, c.case_type, c.priority;
    """, (hero_case_numbers,))
    hero_rows = cur.fetchall()

    hero_audit = []
    for cid, cnum, title, ctype, prio, ent_c in hero_rows:
        cur.execute("""
            SELECT 
                COUNT(DISTINCT e.event_id) AS event_count,
                COUNT(DISTINCT CASE WHEN ep_loc.entity_id IS NOT NULL THEN e.event_id END) AS spatial_event_count,
                COUNT(DISTINCT ep_loc.entity_id) AS loc_count,
                MIN(lower(e.occurred_at)) AS min_t,
                MAX(upper(e.occurred_at)) AS max_t
            FROM civix.case_entity_role cer
            JOIN civix.event_participant ep ON ep.entity_id = cer.entity_id
            JOIN civix.event e ON e.event_id = ep.event_id
            LEFT JOIN civix.event_participant ep_loc ON ep_loc.event_id = e.event_id AND ep_loc.entity_id IN (SELECT entity_id FROM civix.location)
            WHERE cer.case_id = %s::uuid;
        """, (cid,))
        ev_c, spat_ev_c, loc_c, t1, t2 = cur.fetchone()

        cur.execute("""
            SELECT DISTINCT l.location_name, l.location_type, ST_Y(l.geometry), ST_X(l.geometry)
            FROM civix.case_entity_role cer
            JOIN civix.event_participant ep ON ep.entity_id = cer.entity_id
            JOIN civix.event e ON e.event_id = ep.event_id
            JOIN civix.event_participant ep_loc ON ep_loc.event_id = e.event_id
            JOIN civix.location l ON l.entity_id = ep_loc.entity_id
            WHERE cer.case_id = %s::uuid;
        """, (cid,))
        loc_details = cur.fetchall()

        hero_audit.append({
            "case_id": cid,
            "case_number": cnum,
            "title": title,
            "case_type": ctype,
            "priority": prio,
            "entities": ent_c,
            "events": ev_c,
            "spatial_events": spat_ev_c,
            "locations_count": loc_c,
            "locations": [{"name": r[0], "type": r[1], "lat": r[2], "lon": r[3]} for r in loc_details],
            "time_range": f"{t1} to {t2}" if t1 else "None"
        })

    audit["hero_cases"] = hero_audit

    conn.close()
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    run_phase11a_audit()

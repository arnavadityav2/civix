import asyncio
import sys
import os
import json
import math
import hashlib
from typing import Dict, Any, List, Set, Tuple

sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine
from scripts.hero_protection import get_protected_hero_case_ids, build_hero_world_snapshot

# Haversine distance in km
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def run_full_audit():
    results = {}
    hero_ids = get_protected_hero_case_ids()
    hero_ids_str = ", ".join(f"'{h}'::uuid" for h in hero_ids)

    async with engine.connect() as conn:
        # 1. Hero Snapshot Check
        snapshot = await build_hero_world_snapshot(conn)
        results["hero_snapshot_hash"] = snapshot["overall_hash"]
        results["hero_hash_match"] = (snapshot["overall_hash"] == "e520f5a618dc553b4d0b7cfb2579b5e37a56eb3e0c220d75b7677a5d7816369e")
        results["hero_table_counts"] = {k: snapshot[k]["count"] for k in snapshot if k != "overall_hash"}

        # 2. Case Population
        res_cases = await conn.execute(text("SELECT case_id::text, case_number, title, case_type, priority, status, jurisdiction, investigating_unit, opened_at::text FROM civix.investigative_case;"))
        all_cases = [dict(r._mapping) for r in res_cases.fetchall()]
        hero_cases = [c for c in all_cases if c["case_id"].lower() in hero_ids]
        synth_cases = [c for c in all_cases if c["case_id"].lower() not in hero_ids]

        results["total_cases"] = len(all_cases)
        results["hero_cases_count"] = len(hero_cases)
        results["synth_cases_count"] = len(synth_cases)

        # Case type distribution
        case_types = {}
        for c in synth_cases:
            ct = c["case_type"]
            case_types[ct] = case_types.get(ct, 0) + 1
        results["synth_case_types"] = case_types

        # Police station distribution
        st_counts = {}
        for c in synth_cases:
            unit = c["investigating_unit"] or "Unassigned"
            st_counts[unit] = st_counts.get(unit, 0) + 1
        results["synth_station_counts"] = st_counts

        # 3. Events Audit & Event-Level Spatial Sequence Audit
        res_ev = await conn.execute(text(f"""
            SELECT el.case_id::text, el.event_id::text, e.event_type, lower(e.occurred_at)::text as occurred_at, e.description,
                   el.location_id::text, l.location_name, ST_X(ST_Centroid(l.geometry)) as lon, ST_Y(ST_Centroid(l.geometry)) as lat
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            LEFT JOIN civix.location l ON el.location_id = l.entity_id
            WHERE el.case_id NOT IN ({hero_ids_str})
            ORDER BY el.case_id, lower(e.occurred_at) ASC;
        """))
        synth_event_rows = [dict(r._mapping) for r in res_ev.fetchall()]

        # Group by case
        case_events = {}
        for r in synth_event_rows:
            cid = r["case_id"]
            case_events.setdefault(cid, []).append(r)

        event_counts = [len(evs) for evs in case_events.values()]
        event_counts.sort()
        results["total_synth_events"] = len(synth_event_rows)
        results["min_events_per_case"] = min(event_counts) if event_counts else 0
        results["max_events_per_case"] = max(event_counts) if event_counts else 0
        results["avg_events_per_case"] = len(synth_event_rows) / len(synth_cases) if synth_cases else 0
        results["median_events_per_case"] = event_counts[len(event_counts)//2] if event_counts else 0

        # Detailed Event Spatial Analysis
        cases_with_events = len(case_events)
        cases_1_loc_all = 0
        cases_ge_2_locs = 0
        cases_ge_3_locs = 0
        cases_ge_4_locs = 0
        movement_stats = []

        for cid, evs in case_events.items():
            distinct_coords = set()
            for e in evs:
                if e["lat"] is not None and e["lon"] is not None:
                    distinct_coords.add((round(e["lat"], 5), round(e["lon"], 5)))
            
            num_dist = len(distinct_coords)
            if num_dist == 1:
                cases_1_loc_all += 1
            elif num_dist >= 2:
                cases_ge_2_locs += 1
            if num_dist >= 3:
                cases_ge_3_locs += 1
            if num_dist >= 4:
                cases_ge_4_locs += 1

            # Movement transitions
            total_dist_km = 0.0
            prev_coord = None
            for e in evs:
                if e["lat"] is not None and e["lon"] is not None:
                    curr_coord = (e["lat"], e["lon"])
                    if prev_coord and prev_coord != curr_coord:
                        total_dist_km += haversine(prev_coord[0], prev_coord[1], curr_coord[0], curr_coord[1])
                    prev_coord = curr_coord
            
            movement_stats.append({
                "case_id": cid,
                "total_events": len(evs),
                "distinct_locations": num_dist,
                "total_movement_km": round(total_dist_km, 3)
            })

        results["spatial_event_audit"] = {
            "total_synthetic_cases": len(synth_cases),
            "cases_with_events": cases_with_events,
            "events_with_locations": len([r for r in synth_event_rows if r["location_id"]]),
            "event_location_coverage_pct": (len([r for r in synth_event_rows if r["location_id"]]) / len(synth_event_rows)) * 100 if synth_event_rows else 0,
            "cases_1_distinct_loc_all_events": cases_1_loc_all,
            "cases_ge_2_distinct_locs": cases_ge_2_locs,
            "cases_ge_3_distinct_locs": cases_ge_3_locs,
            "cases_ge_4_distinct_locs": cases_ge_4_locs,
            "pct_cases_single_coord_all_events": (cases_1_loc_all / len(synth_cases)) * 100 if synth_cases else 0,
            "pct_cases_multi_coord_movement": (cases_ge_2_locs / len(synth_cases)) * 100 if synth_cases else 0
        }

        # Check description quality
        generic_desc_count = len([r for r in synth_event_rows if "Event #" in (r.get("description") or "")])
        results["generic_event_description_pct"] = (generic_desc_count / len(synth_event_rows)) * 100 if synth_event_rows else 0

        # 4. FIR Quality Audit
        res_fir = await conn.execute(text(f"""
            SELECT f.fir_id::text, f.case_id::text, f.fir_number, f.police_station, f.district, f.filed_at::text,
                   c.case_number, c.investigating_unit
            FROM civix.fir f
            JOIN civix.investigative_case c ON f.case_id = c.case_id;
        """))
        fir_rows = [dict(r._mapping) for r in res_fir.fetchall()]
        hero_firs = [f for f in fir_rows if f["case_id"].lower() in hero_ids]
        synth_firs = [f for f in fir_rows if f["case_id"].lower() not in hero_ids]

        results["total_firs"] = len(fir_rows)
        results["hero_firs"] = len(hero_firs)
        results["synth_firs"] = len(synth_firs)
        results["synth_fir_station_mismatch"] = len([f for f in synth_firs if f["police_station"] != f["investigating_unit"]])

        # 5. Cross-Case Entity Graph Audit
        res_graph = await conn.execute(text(f"""
            SELECT entity_id::text, COUNT(DISTINCT case_id) as case_count
            FROM civix.case_entity_role
            WHERE case_id NOT IN ({hero_ids_str})
            GROUP BY entity_id;
        """))
        entity_case_counts = [dict(r._mapping) for r in res_graph.fetchall()]
        multi_case_entities = [e for e in entity_case_counts if e["case_count"] > 1]
        degrees = [e["case_count"] for e in multi_case_entities]

        results["graph_audit"] = {
            "total_synthetic_entities_in_roles": len(entity_case_counts),
            "multi_case_entities_count": len(multi_case_entities),
            "max_degree": max(degrees) if degrees else 0,
            "degree_distribution": {d: degrees.count(d) for d in set(degrees)}
        }

        # 6. Investigative Leads Audit
        res_leads = await conn.execute(text(f"""
            SELECT lead_id::text, case_id::text, lead_text, priority, status
            FROM civix.investigative_lead;
        """))
        leads_rows = [dict(r._mapping) for r in res_leads.fetchall()]
        hero_leads = [l for l in leads_rows if l["case_id"] and l["case_id"].lower() in hero_ids]
        synth_leads = [l for l in leads_rows if l["case_id"] and l["case_id"].lower() not in hero_ids]

        results["total_leads"] = len(leads_rows)
        results["hero_leads"] = len(hero_leads)
        results["synth_leads"] = len(synth_leads)

        # 7. Neo4j Status Check
        try:
            from civix_api.database import neo4j_driver
            if neo4j_driver:
                async with neo4j_driver.session() as session:
                    res_n4j = await session.run("MATCH (n) RETURN count(n) as cnt")
                    rec = await res_n4j.single()
                    results["neo4j_status"] = f"ONLINE (node count: {rec['cnt']})"
            else:
                results["neo4j_status"] = "OFFLINE (driver None)"
        except Exception as ex:
            results["neo4j_status"] = f"OFFLINE ({str(ex)})"

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(run_full_audit())

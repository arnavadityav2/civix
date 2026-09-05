import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine
from scripts.hero_protection import get_protected_hero_case_ids

async def main():
    hero_ids = get_protected_hero_case_ids()
    hero_ids_str = ", ".join(f"'{h}'::uuid" for h in hero_ids)

    async with engine.connect() as conn:
        # Pick 1 random synthetic case
        res = await conn.execute(text(f"""
            SELECT case_id::text, case_number, title, case_type, priority, status, jurisdiction, investigating_unit, opened_at::text
            FROM civix.investigative_case
            WHERE case_id NOT IN ({hero_ids_str})
            ORDER BY RANDOM()
            LIMIT 1;
        """))
        case_row = dict(res.fetchone()._mapping)
        cid = case_row["case_id"]

        # Fetch FIR
        res_fir = await conn.execute(text("SELECT fir_number, police_station, district, filed_at::text FROM civix.fir WHERE case_id = CAST(:cid AS uuid)"), {"cid": cid})
        fir_row = [dict(r._mapping) for r in res_fir.fetchall()]

        # Fetch Event Locations & Geometries
        res_loc = await conn.execute(text("""
            SELECT l.location_name, l.location_type, ST_X(ST_Centroid(l.geometry)) as lon, ST_Y(ST_Centroid(l.geometry)) as lat
            FROM civix.event_location el
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE el.case_id = CAST(:cid AS uuid)
            LIMIT 5;
        """), {"cid": cid})
        loc_rows = [dict(r._mapping) for r in res_loc.fetchall()]

        # Fetch Events
        res_ev = await conn.execute(text("""
            SELECT e.event_id::text, e.event_type, lower(e.occurred_at)::text as occurred_at, e.description
            FROM civix.event_location el
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE el.case_id = CAST(:cid AS uuid)
            ORDER BY lower(e.occurred_at) ASC;
        """), {"cid": cid})
        event_rows = [dict(r._mapping) for r in res_ev.fetchall()]

        # Fetch Case Entities / Roles
        res_ent = await conn.execute(text("""
            SELECT entity_id::text, role
            FROM civix.case_entity_role
            WHERE case_id = CAST(:cid AS uuid);
        """), {"cid": cid})
        role_rows = [dict(r._mapping) for r in res_ent.fetchall()]

        print(json.dumps({
            "case": case_row,
            "fir": fir_row,
            "locations": loc_rows,
            "events": event_rows,
            "entity_roles": role_rows
        }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

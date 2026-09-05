import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine
from scripts.hero_protection import get_protected_hero_case_ids

async def resolve_entity_info(conn, entity_id: str):
    # Try person
    r = await conn.execute(text("SELECT display_name, gender FROM civix.person WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "PERSON", "name": row[0], "details": f"Gender: {row[1]}"}
    
    # Try phone_number
    r = await conn.execute(text("SELECT msisdn, operator FROM civix.phone_number WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "PHONE", "name": f"+91-{row[0]}", "details": f"Operator: {row[1]}"}

    # Try organization
    r = await conn.execute(text("SELECT legal_name, org_type FROM civix.organization WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "ORGANIZATION", "name": row[0], "details": f"Type: {row[1]}"}

    # Try vehicle
    r = await conn.execute(text("SELECT registration_number, make, model FROM civix.vehicle WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "VEHICLE", "name": row[0], "details": f"{row[1]} {row[2]}"}

    # Try financial account
    r = await conn.execute(text("SELECT masked_number, bank_name FROM civix.financial_account WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "FINANCIAL_ACCOUNT", "name": row[0], "details": f"Bank: {row[1]}"}

    # Try device
    r = await conn.execute(text("SELECT COALESCE(imei, mac_address, 'Device'), device_type FROM civix.device WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "DEVICE", "name": row[0], "details": f"Type: {row[1]}"}

    return {"type": "UNKNOWN", "name": f"Entity-{entity_id[:8]}", "details": "N/A"}

async def main():
    hero_ids = get_protected_hero_case_ids()
    hero_ids_str = ", ".join(f"'{h}'::uuid" for h in hero_ids)

    async with engine.connect() as conn:
        # Pick 1 random synthetic case excluding SYN-2025-103
        res = await conn.execute(text(f"""
            SELECT case_id::text, case_number, title, case_type, priority, status, jurisdiction, investigating_unit, opened_at::text
            FROM civix.investigative_case
            WHERE case_id NOT IN ({hero_ids_str}) AND case_number != 'SYN-2025-103'
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
            LIMIT 1;
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
        roles = res_ent.fetchall()
        resolved_roles = []
        for r in roles:
            eid, role = r[0], r[1]
            info = await resolve_entity_info(conn, eid)
            resolved_roles.append({
                "entity_id": eid,
                "role": role,
                "type": info["type"],
                "name": info["name"],
                "details": info["details"]
            })

        print(json.dumps({
            "case": case_row,
            "fir": fir_row,
            "location": loc_rows[0] if loc_rows else None,
            "events": event_rows,
            "entities": resolved_roles
        }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

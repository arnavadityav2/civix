import asyncio
import sys
import os
import json
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

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
    r = await conn.execute(text("SELECT primary_identifier, device_type FROM civix.device WHERE entity_id = CAST(:eid AS uuid)"), {"eid": entity_id})
    row = r.fetchone()
    if row:
        return {"type": "DEVICE", "name": row[0], "details": f"Device: {row[1]}"}

    return {"type": "UNKNOWN", "name": f"Entity-{entity_id[:8]}", "details": "N/A"}

async def main():
    async with engine.connect() as conn:
        cid = "6390a55f-8689-274c-38ac-222fc799cdb1" # SYN-2025-103
        res_ent = await conn.execute(text("""
            SELECT entity_id::text, role
            FROM civix.case_entity_role
            WHERE case_id = CAST(:cid AS uuid);
        """), {"cid": cid})
        roles = res_ent.fetchall()
        print(f"Resolved Entities for Case SYN-2025-103:")
        for r in roles:
            eid, role = r[0], r[1]
            info = await resolve_entity_info(conn, eid)
            print(f"  - Role: {role:18} | Type: {info['type']:16} | Name/Value: {info['name']:25} | Details: {info['details']}")

if __name__ == "__main__":
    asyncio.run(main())

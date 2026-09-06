import asyncio
import json
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def main():
    with open(r"C:\data\civix_demo\biometric_demo\index.json") as f:
        index_data = json.load(f)
    
    pids = list(set(e["person_id"] for e in index_data["entries"]))
    print(f"Cohort PIDs ({len(pids)}):", pids)

    async with AsyncSessionLocal() as session:
        for pid in pids:
            r_person = await session.execute(text("SELECT display_name FROM civix.person WHERE entity_id = :pid"), {"pid": pid})
            pname = r_person.scalar()
            
            r_roles = await session.execute(text("SELECT role::text FROM civix.case_entity_role WHERE entity_id = :pid"), {"pid": pid})
            roles = [row[0] for row in r_roles.fetchall()]
            print(f"PID: {pid} | Name: {pname} | Roles: {roles}")

if __name__ == '__main__':
    asyncio.run(main())

import asyncio
import os
import json
import uuid
from datetime import datetime, date
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, bytes):
            return obj.hex()
        return super().default(obj)

async def main():
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"
    engine = create_async_engine(url)
    
    output = {}
    async with engine.connect() as conn:
        case = await conn.execute(text("SELECT * FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'"))
        rows = case.fetchall()
        if not rows:
            print("Case not found.")
            return
        case_id = rows[0][0]
        output['case'] = dict(rows[0]._mapping)
        
        # Entities via case_entity_role
        roles_res = await conn.execute(text(f"""
            SELECT cer.role, cer.role_basis, e.entity_id, e.entity_type 
            FROM civix.case_entity_role cer
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            WHERE cer.case_id = '{case_id}'
        """))
        roles = [dict(r._mapping) for r in roles_res.fetchall()]
        output['entities'] = roles
        
        # Persons
        persons = []
        vehicles = []
        for r in roles:
            if r['entity_type'] == 'PERSON':
                pres = await conn.execute(text(f"SELECT * FROM civix.person WHERE entity_id = '{r['entity_id']}'"))
                p_rows = pres.fetchall()
                if p_rows:
                    p_dict = dict(p_rows[0]._mapping)
                    p_dict['role'] = r['role']
                    persons.append(p_dict)
            elif r['entity_type'] == 'VEHICLE':
                vres = await conn.execute(text(f"SELECT * FROM civix.vehicle WHERE entity_id = '{r['entity_id']}'"))
                v_rows = vres.fetchall()
                if v_rows:
                    v_dict = dict(v_rows[0]._mapping)
                    v_dict['role'] = r['role']
                    vehicles.append(v_dict)
                    
        output['persons'] = persons
        output['vehicles'] = vehicles
        
        # Evidence via evidence_instance
        try:
            ev_res = await conn.execute(text(f"""
                SELECT ei.*, ea.* 
                FROM civix.evidence_instance ei
                JOIN civix.evidence_artifact ea ON ei.artifact_id = ea.artifact_id
                WHERE ei.case_id = '{case_id}'
            """))
            output['evidence'] = [dict(r._mapping) for r in ev_res.fetchall()]
        except Exception as e:
            output['evidence_error'] = str(e)
        
        # Assertions via authorized_case_ids array
        try:
            ass_res = await conn.execute(text(f"""
                SELECT * FROM civix.assertion 
                WHERE '{case_id}' = ANY(authorized_case_ids)
            """))
            output['assertions'] = [dict(r._mapping) for r in ass_res.fetchall()]
        except Exception as e:
            output['assertions_error'] = str(e)
            
        # Try to find FIR
        try:
            fir_res = await conn.execute(text(f"""
                SELECT f.* FROM civix.fir f
                JOIN civix.case_link cl ON cl.target_id = f.fir_id
                WHERE cl.case_id = '{case_id}'
            """))
            output['fir'] = [dict(r._mapping) for r in fir_res.fetchall()]
        except Exception as e:
            output['fir_error'] = str(e)

    with open("scratch/case_full_dump.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, cls=CustomEncoder)

if __name__ == "__main__":
    asyncio.run(main())

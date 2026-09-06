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
        return super().default(obj)

async def main():
    url = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"
    engine = create_async_engine(url)
    
    output = {}
    async with engine.connect() as conn:
        # Get tables
        tables = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix'"))
        output['tables'] = [r[0] for r in tables]
        
        # Query investigative_case
        case = await conn.execute(text("SELECT * FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'"))
        rows = case.fetchall()
        if not rows:
            print("Case not found.")
            return
            
        case_id = rows[0][0]
        output['case_id'] = str(case_id)
        
        output['case'] = dict(rows[0]._mapping)
        
        # In civix schema, tables are likely: entity, event, evidence, assertion, etc.
        # But wait, looking at my previous run, evidence table has `case_number` in `audit_raw_results.json`... wait no.
        # Let's query them by `case_id`
        
        for table in ['entity', 'event', 'evidence', 'assertion', 'cctv_registry']:
            try:
                res = await conn.execute(text(f"SELECT * FROM civix.{table} WHERE case_id = '{case_id}' LIMIT 50"))
                output[table] = [dict(r._mapping) for r in res.fetchall()]
            except Exception as e:
                output[table] = {"error": str(e)}

    with open("scratch/db_dump_output.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, cls=CustomEncoder)

if __name__ == "__main__":
    asyncio.run(main())

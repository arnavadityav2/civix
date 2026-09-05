import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    
    rows = await c.fetch("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema='civix' AND data_type='uuid'
    """)
    
    source_ids = await c.fetch("SELECT DISTINCT source_record_id FROM civix.evidence_instance WHERE source_record_id IS NOT NULL")
    source_ids = [r[0] for r in source_ids]
    
    for r in rows:
        t = r['table_name']
        col = r['column_name']
        if col == 'source_record_id' or t == 'evidence_instance': continue
        
        try:
            hits = await c.fetchval(f"SELECT COUNT(*) FROM civix.{t} WHERE {col} = ANY($1)", source_ids)
            if hits > 0:
                print(f"source_record_id points to {hits} rows in {t}.{col}")
        except Exception as e:
            pass
            
    await c.close()
asyncio.run(run())

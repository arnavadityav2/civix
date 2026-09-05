import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    
    rows = await c.fetch("SELECT instance_id, case_id, source_record_id FROM civix.evidence_instance LIMIT 5")
    for r in rows:
        print(dict(r))
        
    print("Checking if source_record_id points to entity...")
    rows2 = await c.fetch("SELECT COUNT(*) FROM civix.evidence_instance e JOIN civix.entity ent ON e.source_record_id = ent.entity_id")
    print(f"Evidence pointing to entities: {rows2[0][0]}")

    print("Checking if source_record_id points to event...")
    rows3 = await c.fetch("SELECT COUNT(*) FROM civix.evidence_instance e JOIN civix.event ev ON e.source_record_id = ev.event_id")
    print(f"Evidence pointing to events: {rows3[0][0]}")

    print("Checking if source_record_id points to assertion...")
    rows4 = await c.fetch("SELECT COUNT(*) FROM civix.evidence_instance e JOIN civix.assertion a ON e.source_record_id = a.assertion_id")
    print(f"Evidence pointing to assertions: {rows4[0][0]}")
    
    print("Checking if source_record_id points to lead...")
    rows5 = await c.fetch("SELECT COUNT(*) FROM civix.evidence_instance e JOIN civix.investigative_lead l ON e.source_record_id = l.lead_id")
    print(f"Evidence pointing to leads: {rows5[0][0]}")
    
    print("Checking if source_record_id points to fir...")
    rows6 = await c.fetch("SELECT COUNT(*) FROM civix.evidence_instance e JOIN civix.fir f ON e.source_record_id = f.fir_id")
    print(f"Evidence pointing to firs: {rows6[0][0]}")

    await c.close()

asyncio.run(run())

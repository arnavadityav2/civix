import asyncio
import asyncpg
import json

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cid = "1346a86d-267a-a635-9d62-e34c76ecd24f"
    
    print("==========================================================================")
    print("           CIV-2012-001 DATABASE COUNT & AGGREGATION AUDIT                ")
    print("==========================================================================")

    # 1. Direct case_entity_role count
    cer_count = await conn.fetchval("SELECT COUNT(*) FROM civix.case_entity_role WHERE case_id = $1", cid)
    cer_dist_count = await conn.fetchval("SELECT COUNT(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1", cid)
    print(f"case_entity_role: total={cer_count}, distinct_entity_id={cer_dist_count}")

    # 2. Entity types breakdown for CIV-2012-001
    types_res = await conn.fetch("""
        SELECT e.entity_type, COUNT(*) as cnt, COUNT(DISTINCT cer.entity_id) as dist_cnt
        FROM civix.case_entity_role cer
        JOIN civix.entity e ON cer.entity_id = e.entity_id
        WHERE cer.case_id = $1
        GROUP BY e.entity_type
    """, cid)
    print("\nEntity Types Breakdown in case_entity_role:")
    for r in types_res:
        print(f"  - {r['entity_type']}: total={r['cnt']}, distinct={r['dist_cnt']}")

    # 3. Evidence instance count
    ev_count = await conn.fetchval("SELECT COUNT(*) FROM civix.evidence_instance WHERE case_id = $1", cid)
    print(f"\nevidence_instance count: {ev_count}")

    # 4. Event Location count
    el_count = await conn.fetchval("SELECT COUNT(*) FROM civix.event_location WHERE case_id = $1", cid)
    print(f"event_location count: {el_count}")

    # 5. Cell Tower count
    tower_count = await conn.fetchval("""
        SELECT COUNT(DISTINCT ct.tower_id) 
        FROM civix.cell_tower ct
        JOIN civix.event_location el ON ST_DWithin(ct.location, el.location, 0.05)
        WHERE el.case_id = $1
    """, cid)
    print(f"cell_tower near event locations count: {tower_count}")

    # 6. Check what queries are executed when opening case workspace!
    print("==========================================================================")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())

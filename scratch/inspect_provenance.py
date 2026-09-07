import asyncio
import asyncpg

async def inspect_provenance():
    conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
    
    # 1. Columns of investigative_case
    cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='investigative_case';")
    print("Columns of civix.investigative_case:")
    for c in cols:
        print(f" - {c['column_name']}: {c['data_type']}")

    # 2. Check provenance values in investigative_case or evidence_generation_manifest
    try:
        manifests = await conn.fetch("SELECT * FROM civix.evidence_generation_manifest LIMIT 5;")
        print("\nManifests in civix.evidence_generation_manifest:")
        for m in manifests:
            print(" -", dict(m))
    except Exception as e:
        print("Manifest table error:", e)

    # 3. Check cases in civix.investigative_case
    cases = await conn.fetch("SELECT case_id, case_number, title, case_type, priority FROM civix.investigative_case;")
    print(f"\nTotal Cases in DB: {len(cases)}")
    
    # Check if there is any column or join that indicates Golden/Hero provenance
    provenance_table_check = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='civix' AND (table_name LIKE '%prov%' OR table_name LIKE '%manifest%' OR table_name LIKE '%gold%');")
    print("\nRelated Tables:")
    for t in provenance_table_check:
        print(" -", t['table_name'])
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(inspect_provenance())

import asyncio
import time
from uuid import uuid4
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal
from civix_api.services.entity_resolver import EntityResolver

async def generate_benchmark_data(session, size, benchmark_id, sys_user_id):
    print(f"\nGenerating {size} identities...")
    
    # We will generate pairs of Person + SourceIdentity that match
    batch_size = 500
    for i in range(0, size, batch_size):
        persons = []
        sources = []
        phones = []
        assertions = []
        entities = []
        
        for j in range(min(batch_size, size - i)):
            idx = i + j
            p_id = uuid4()
            si_id = uuid4()
            ph_id = uuid4()
            
            name = "RAHUL SHARMA" if idx % 10 == 0 else f"USER {benchmark_id}_{idx}"
            
            entities.extend([{"id": p_id, "type": "PERSON"}, {"id": si_id, "type": "SOURCE_IDENTITY"}, {"id": ph_id, "type": "PHONE_NUMBER"}])
            persons.append({"id": p_id, "name": name})
            sources.append({"id": si_id, "name": name, "rec": p_id})
            phones.append({"id": ph_id, "ph": f"91999{idx:07d}"})
            
            assertions.append({"id": uuid4(), "sub": p_id, "pred": "OWNS", "obj": ph_id, "ast": sys_user_id, "epistemic_status": "CONFIRMED"})
            assertions.append({"id": uuid4(), "sub": si_id, "pred": "OWNS", "obj": ph_id, "ast": sys_user_id, "epistemic_status": "CONFIRMED"})
            
        await session.execute(text("INSERT INTO civix.entity (entity_id, entity_type) VALUES (:id, :type) ON CONFLICT DO NOTHING"), entities)
        
        # Insert source and source_record for these identities
        source_id = uuid4()
        await session.execute(text("INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score) VALUES (:id, :name, 'OTHER', 1.0) ON CONFLICT DO NOTHING"), [{"id": source_id, "name": f"TEST_SRC_{source_id.hex[:8]}"}])
        await session.execute(text("INSERT INTO civix.source_record (source_record_id, source_id, record_type) VALUES (:id, :sid, 'TEST')"), [{"id": s["rec"], "sid": source_id} for s in sources])
        
        await session.execute(text("INSERT INTO civix.person (entity_id, display_name) VALUES (:id, :name)"), persons)
        await session.execute(text("INSERT INTO civix.source_identity (entity_id, source_record_id, identifier_type, raw_identifier, observed_at) VALUES (:id, :rec, 'NAME', :name, NOW())"), sources)
        await session.execute(text("INSERT INTO civix.phone_number (entity_id, msisdn) VALUES (:id, :ph) ON CONFLICT DO NOTHING"), phones)
        await session.execute(text("INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_entity_id, asserted_by, epistemic_status) VALUES (:id, :sub, :pred, :obj, :ast, :epistemic_status)"), assertions)
        
    await session.commit()
    print("Generation complete.")

async def run_benchmark():
    sizes = [1000, 5000, 10000]
    
    for size in sizes:
        print(f"\n=== BENCHMARK: {size} IDENTITIES ===")
        async with AsyncSessionLocal() as session:
            sys_user_id = uuid4()
            await session.execute(text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:id, :auth, :uname, 'Sys', 'ANALYST') ON CONFLICT DO NOTHING"), {"id": sys_user_id, "auth": f"auth_{sys_user_id}", "uname": f"user_{sys_user_id}"})
            
            benchmark_id = uuid4().hex[:6]
            await generate_benchmark_data(session, size, benchmark_id, sys_user_id)
            
            run_id = uuid4()
            await session.execute(text("INSERT INTO civix.analysis_run (run_id, model_name, model_version, algorithm_type, initiated_by, started_at) VALUES (:rid, 'c2_benchmark', 'v1', 'algo', (SELECT user_id FROM civix.civix_user LIMIT 1), NOW())"), {"rid": run_id})
            await session.commit()
            
            resolver = EntityResolver(session)
            
            start_time = time.time()
            stats = await resolver.run(run_id)
            await session.commit()
            end_time = time.time()
            
            duration = end_time - start_time
            print(f"Execution time: {duration:.3f} seconds")
            print(f"Total candidates: {stats.get('total_candidates', 0)}")
            print(f"Stats: {stats}")
            
            if duration > 5.0:
                print("WARNING: Exceeded 5s performance target.")
            else:
                print("PERFORMANCE: PASS (<5s)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())

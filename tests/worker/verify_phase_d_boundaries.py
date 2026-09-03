import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from neo4j import AsyncGraphDatabase

from civix_api.config import settings

POSTGRES_URI = settings.civix_database_url
NEO4J_URI = settings.neo4j_uri
NEO4J_USER = settings.neo4j_user
NEO4J_PASS = settings.neo4j_password

async def verify_boundaries():
    print("=== CIVIX 2.0 PHASE D BOUNDARY CHECK ===")
    
    # 1. PostgreSQL check
    engine = create_async_engine(POSTGRES_URI)
    async with engine.connect() as conn:
        res_cand = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_match_candidate"))
        cand_count = res_cand.scalar()
        
        res_obs = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_observation"))
        obs_count = res_obs.scalar()
        
        res_cams = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_camera"))
        cam_count = res_cams.scalar()

        res_jobs = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_search_job"))
        job_count = res_jobs.scalar()
        
        print(f"cctv_camera count: {cam_count}")
        print(f"cctv_search_job count: {job_count}")
        print(f"cctv_match_candidate count: {cand_count} (Expected: 0)")
        print(f"cctv_observation count: {obs_count} (Expected: 0)")
        
        assert cand_count == 0, f"VIOLATION: cctv_match_candidate is {cand_count}, expected 0!"
        assert obs_count == 0, f"VIOLATION: cctv_observation is {obs_count}, expected 0!"

    await engine.dispose()
    
    # 2. Neo4j check
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    async with driver.session() as session:
        result = await session.run("MATCH ()-[r:SAME_AS]->() RETURN count(r) as c")
        record = await result.single()
        same_as_count = record["c"]
        print(f"Neo4j SAME_AS relationship count: {same_as_count} (Expected: 0)")
        assert same_as_count == 0, f"VIOLATION: Neo4j SAME_AS count is {same_as_count}, expected 0!"

    await driver.close()
    print("ALL BOUNDARY CONSTRAINTS VERIFIED SUCCESSFULLY. PASS.")

if __name__ == "__main__":
    asyncio.run(verify_boundaries())

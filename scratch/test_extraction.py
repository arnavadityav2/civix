import os
import asyncio
import asyncpg
import uuid
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv
import json

from civix_api.database import AsyncSessionLocal
from civix_api.services.nlp.groq_client import call_groq
from civix_api.services.nlp.validator import validate
from civix_api.services.nlp.entity_mapper import map_extraction_to_db

load_dotenv()
os.environ["CIVIX_USE_GROQ_PROVIDER"] = "1"

import asyncpg

async def process_target(session: AsyncSession, user_id: UUID, search_string: str, label: str):
    print(f"\n--- Processing Target: {label} ---")
    
    # 1. Find the observation and related artifact/instance (bypassing RLS with asyncpg)
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    row = await conn.fetchrow("""
        SELECT o.observation_id, o.instance_id, o.observation_text, i.artifact_id, i.case_id
        FROM civix.observation o
        JOIN civix.evidence_instance i ON o.instance_id = i.instance_id
        WHERE o.observation_text ILIKE $1
        LIMIT 1
    """, f"%{search_string}%")
    await conn.close()
    
    if not row:
        print(f"Skipping: {label} - No observation found matching search string.")
        return
        
    observation_id = row['observation_id']
    instance_id = row['instance_id']
    text_content = row['observation_text']
    artifact_id = row['artifact_id']
    case_id = row['case_id']
    
    # Get a user who actually has access to this case to satisfy RLS
    conn2 = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    user_row = await conn2.fetchrow("""
        SELECT user_id FROM civix.case_access WHERE case_id = $1 LIMIT 1
    """, case_id)
    await conn2.close()
    
    if not user_row:
        print(f"Skipping: {label} - No user with case_access found for case_id={case_id}")
        return
        
    user_id = user_row['user_id']
    text_content = row['observation_text']
    
    print(f"Found Observation ID: {observation_id}")
    print(f"Artifact ID: {artifact_id}, Instance ID: {instance_id}")
    print(f"Text snippet: {text_content[:150]}...")
    
    # Set RLS context variables
    await session.execute(text(f"SELECT set_config('civix.current_user_id', '{user_id}', false), set_config('app.current_user_id', '{user_id}', false)"))
    
    # 2. Call Groq
    print("Calling Groq API...")
    raw_chunks = call_groq(text_content, case_context="Criminal investigation")
    
    print(f"Groq returned {len(raw_chunks)} chunk(s).")
    
    # 3. Validate and Map
    for idx, chunk in enumerate(raw_chunks):
        print(f"\nValidating chunk {idx+1}...")
        merged_result = validate(chunk)
        print("Validation Result (Entities/Relationships/Temporal):")
        print(f"  Entities: {len(merged_result.entities)}")
        print(f"  Relationships: {len(merged_result.relationships)}")
        
        # Look for KNOWN_ASSOCIATE_OF
        for r in merged_result.relationships:
            subj_name = next((e.canonical_name for e in merged_result.entities if e.local_id == r.subject_local_id), r.subject_local_id)
            obj_name = next((e.canonical_name for e in merged_result.entities if e.local_id == r.object_local_id), r.object_local_id)
            print(f"  --> {subj_name} --[{r.predicate}]--> {obj_name}")
            
        # Prevent uniqueness collision for the same instance_id
        import uuid
        run_suffix = str(uuid.uuid4())[:8]
        for e in merged_result.entities:
            old_id = e.local_id
            e.local_id = f"{e.local_id}_{run_suffix}"
            for r in merged_result.relationships:
                if r.subject_local_id == old_id:
                    r.subject_local_id = e.local_id
                if r.object_local_id == old_id:
                    r.object_local_id = e.local_id
            
        # Find a valid source_id
        source_query = text("SELECT source_id FROM civix.source LIMIT 1")
        source_result = await session.execute(source_query)
        source_row = source_result.fetchone()
        if not source_row:
            print(f"Skipping: {label} - No source found in db")
            return
        nlp_source_id = source_row.source_id
            
        print("Mapping to database...")
        db_result = await map_extraction_to_db(
            session=session,
            result=merged_result,
            instance_id=instance_id,
            case_id=case_id,
            artifact_id=artifact_id,
            extracted_text=text_content,
            user_id=user_id,
            nlp_source_id=nlp_source_id
        )
        print("DB Result Summary:", db_result)
        
    await session.commit()
    print(f"Finished processing {label}")

async def main():
    async with AsyncSessionLocal() as session:
        # Find a valid system user or SUPERVISOR
        user_query = text("SELECT user_id FROM civix.civix_user LIMIT 1")
        result = await session.execute(user_query)
        user_row = result.fetchone()
        if not user_row:
            print("No auth user found!")
            return
        user_id = user_row.user_id
        # Target A: Vikram -> Neha Coordinator
        await process_target(session, user_id, "Neha Coordinator", "Target A (Neha Coordinator)")
        
        print("Sleeping 40s to avoid TPM rate limits...")
        await asyncio.sleep(40)
        # Target B: Vikram -> Global Exports
        await process_target(session, user_id, "Global Exports Pvt Ltd", "Target B (Global Exports)")
        
        print("Sleeping 40s to avoid TPM rate limits...")
        await asyncio.sleep(40)
        # What about Negative controls? 
        await process_target(session, user_id, "Rahul Sharma", "Negative A (Rahul Sharma)")
        
        print("Sleeping 40s to avoid TPM rate limits...")
        await asyncio.sleep(40)
        await process_target(session, user_id, "Drug Trafficking Cartel", "Negative B (Drug Trafficking Cartel)")

if __name__ == "__main__":
    asyncio.run(main())

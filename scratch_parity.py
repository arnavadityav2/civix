import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from civix_api.services.feature_extractor import extract_candidate_features

async def run_parity():
    url = "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
    engine = create_async_engine(url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get one valid candidate with some events
        result = await session.execute(text("""
            SELECT p.entity_id 
            FROM civix.person p
            JOIN civix.event_participant ep ON ep.entity_id = p.entity_id
            GROUP BY p.entity_id
            ORDER BY count(ep.event_id) DESC
            LIMIT 1
        """))
        cid = result.scalar()
        if not cid:
            print("No candidate found in civix_test database.")
            return
            
        print(f"Fixture entity: Person")
        print(f"Entity ID: {cid}")
        
        # Get run_id or source info
        result_run = await session.execute(text("SELECT generation_run_id FROM civix.person WHERE entity_id = :cid"), {"cid": cid})
        run_id = result_run.scalar()
        print(f"Source dataset/generation run: {run_id}")
        
        # Extract features
        features = await extract_candidate_features(session, [str(cid)])
        print("\n--- EXTRACTED FEATURES ---")
        if features and str(cid) in features:
            for k, v in features[str(cid)].items():
                print(f"{k}: {v}")
                
if __name__ == "__main__":
    asyncio.run(run_parity())

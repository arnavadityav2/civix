import joblib
import pandas as pd
from civix_api.services.ml_service import MLService
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from civix_api.services.feature_extractor import extract_candidate_features
from uuid import uuid4
import os
os.environ["CIVIX_JWT_SECRET"] = "test_secret"
os.environ["CIVIX_DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_db"

from civix_api.config import settings

async def test_parity():
    engine = create_async_engine(settings.civix_database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get one valid candidate from db that has calls
        result = await session.execute(text("""
            SELECT p.entity_id 
            FROM civix.person p
            JOIN civix.event_participant ep ON ep.entity_id = p.entity_id
            WHERE ep.participant_role = 'CALLER'
            LIMIT 1
        """))
        cid = result.scalar()
        if not cid:
            print("No candidate found.")
            return
            
        features = await extract_candidate_features(session, [str(cid)])
        print(f"Extracted for {cid}:")
        if features and str(cid) in features:
            for k, v in features[str(cid)].items():
                if v != 0:
                    print(f"  {k}: {v}")
                    
if __name__ == "__main__":
    asyncio.run(test_parity())

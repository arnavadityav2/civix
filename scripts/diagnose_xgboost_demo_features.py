import asyncio
import hashlib
import numpy as np
import psycopg2
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker

from civix_api.config import settings
from civix_api.services.feature_extractor import extract_candidate_features
from civix_api.services.ml_service import MLService, EXPECTED_FEATURES

async def diagnose_xgboost_demo_features():
    print("==========================================================")
    print("XGBOOST FEATURE VECTOR DIAGNOSTIC AUDIT (50 DEMO PERSONS)")
    print("==========================================================")

    # 1. Connect to civix_demo PostgreSQL and fetch 50 distinct Person IDs
    pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT DISTINCT entity_id::TEXT FROM civix.person LIMIT 50;")
    person_ids = [r[0] for r in pg_cur.fetchall()]
    pg_conn.close()

    print(f"1. Unique Person IDs Fetched : {len(person_ids)}")
    assert len(person_ids) == len(set(person_ids)), "Person IDs must be distinct."

    # 2. Initialize MLService
    MLService.initialize()

    # 3. Extract real candidate features using feature_extractor
    engine = create_async_engine(settings.civix_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        candidate_features = await extract_candidate_features(session, person_ids)

    await engine.dispose()

    # 4. Analyze Feature Matrix
    feature_matrix = []
    vector_hashes = []

    for pid in person_ids:
        feats = candidate_features.get(pid, {})
        row = [float(feats.get(f, 0.0)) for f in EXPECTED_FEATURES]
        feature_matrix.append(row)
        
        # Compute SHA-256 hash of feature vector
        v_str = ",".join(f"{x:.6f}" for x in row)
        v_hash = hashlib.sha256(v_str.encode()).hexdigest()
        vector_hashes.append(v_hash)

    feature_matrix = np.array(feature_matrix)
    unique_hashes = set(vector_hashes)

    print(f"2. Feature Matrix Shape     : {feature_matrix.shape}")
    print(f"3. Unique Feature Vectors   : {len(unique_hashes)} / {len(person_ids)}")

    # Check if feature vectors are distinct
    if len(unique_hashes) == 1:
        print("\n[WARNING / STOP] unique_feature_vectors == 1. All candidate feature vectors are identical!")
    else:
        print(f"   - Distinct vector profiles detected across candidates.")

    # 5. Run XGBoost Inference
    results = MLService.predict_leads(candidate_features)
    scores = [r["score"] for r in results]

    score_min = float(np.min(scores))
    score_max = float(np.max(scores))
    score_mean = float(np.mean(scores))
    score_median = float(np.median(scores))
    score_std = float(np.std(scores))

    print("\n4. Model Scoring Output Summary:")
    print(f"   - Score Min    : {score_min:.6f}")
    print(f"   - Score Max    : {score_max:.6f}")
    print(f"   - Score Mean   : {score_mean:.6f}")
    print(f"   - Score Median : {score_median:.6f}")
    print(f"   - Score StdDev : {score_std:.6f}")

    print("\n==========================================================")
    print("[PASS] XGBOOST FEATURE VECTOR DIAGNOSTIC AUDIT COMPLETED")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(diagnose_xgboost_demo_features())

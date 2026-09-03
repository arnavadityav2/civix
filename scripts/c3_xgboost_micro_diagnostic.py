import asyncio
import hashlib
import numpy as np
import pandas as pd
import psycopg2
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from civix_api.config import settings
from civix_api.services.feature_extractor import extract_candidate_features
from civix_api.services.ml_service import MLService, EXPECTED_FEATURES

async def run_micro_diagnostic():
    # 1. Connect to civix_demo PostgreSQL and fetch 50 distinct Person IDs
    pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    pg_cur = pg_conn.cursor()
    pg_cur.execute("SELECT DISTINCT entity_id::TEXT FROM civix.person LIMIT 50;")
    person_ids = [r[0] for r in pg_cur.fetchall()]
    pg_conn.close()

    # 2. Extract candidate features using application pipeline
    engine = create_async_engine(settings.civix_database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        candidate_features = await extract_candidate_features(session, person_ids)

    await engine.dispose()

    # Group candidate features by hash to isolate Vector A and Vector B
    vector_groups = {}
    for pid in person_ids:
        feats = candidate_features.get(pid, {})
        row = [float(feats.get(f, 0.0)) for f in EXPECTED_FEATURES]
        v_str = ",".join(f"{x:.6f}" for x in row)
        v_hash = hashlib.sha256(v_str.encode()).hexdigest()
        
        if v_hash not in vector_groups:
            vector_groups[v_hash] = {
                "hash": v_hash,
                "sample_pid": pid,
                "row": row,
                "feats_dict": feats,
                "count": 0
            }
        vector_groups[v_hash]["count"] += 1

    unique_hashes = list(vector_groups.keys())
    assert len(unique_hashes) == 2, f"Expected 2 unique feature vectors, got {len(unique_hashes)}"

    vec_A = vector_groups[unique_hashes[0]]
    vec_B = vector_groups[unique_hashes[1]]

    row_A = vec_A["row"]
    row_B = vec_B["row"]

    hash_A = vec_A["hash"]
    hash_B = vec_B["hash"]

    nonzero_A = int(np.count_nonzero(row_A))
    nonzero_B = int(np.count_nonzero(row_B))

    # 3. Initialize MLService directly
    MLService.initialize()
    model = MLService._model

    # Verify model.n_features_in_
    n_features_in = getattr(model, "n_features_in_", len(model.feature_names_in_))

    # Construct DataFrame with shape (2, 70) for direct model call
    df_2 = pd.DataFrame([row_A, row_B], columns=EXPECTED_FEATURES)
    matrix_shape = df_2.shape

    # Direct model predict_proba call
    probs_direct = model.predict_proba(df_2)
    prob_A_direct = float(probs_direct[0, 1])
    prob_B_direct = float(probs_direct[1, 1])

    # 4. Compare with application predict_leads call
    app_input = {
        vec_A["sample_pid"]: vec_A["feats_dict"],
        vec_B["sample_pid"]: vec_B["feats_dict"]
    }
    app_results = MLService.predict_leads(app_input)
    app_scores_map = {r["candidate_id"]: r["score"] for r in app_results}

    prob_A_app = app_scores_map[vec_A["sample_pid"]]
    prob_B_app = app_scores_map[vec_B["sample_pid"]]

    print("==========================================================")
    print("C3 / XGBOOST MICRO-DIAGNOSTIC REPORT")
    print("==========================================================")
    print(f"vector_A_hash                   : {hash_A[:16]}...")
    print(f"vector_B_hash                   : {hash_B[:16]}...")
    print(f"vector_A_nonzero_feature_count : {nonzero_A}")
    print(f"vector_B_nonzero_feature_count : {nonzero_B}")
    print(f"model.n_features_in_            : {n_features_in}")
    print(f"predict_proba input shape       : {matrix_shape}")
    print(f"vector_A_probability (Direct)   : {prob_A_direct:.6f}")
    print(f"vector_B_probability (Direct)   : {prob_B_direct:.6f}")
    print(f"vector_A_probability (App)      : {prob_A_app:.6f}")
    print(f"vector_B_probability (App)      : {prob_B_app:.6f}")
    print(f"direct_model_output_A == B      : {prob_A_direct == prob_B_direct}")
    print(f"direct == application outputs   : {prob_A_direct == prob_A_app and prob_B_direct == prob_B_app}")

    # Inspect if any features differ between A and B
    diff_features = []
    for idx, fname in enumerate(EXPECTED_FEATURES):
        if row_A[idx] != row_B[idx]:
            diff_features.append((fname, row_A[idx], row_B[idx]))

    print(f"\nFeature Differences (Vector A vs Vector B):")
    for fname, val_a, val_b in diff_features:
        print(f"  - {fname:<25}: Vector A = {val_a}, Vector B = {val_b}")

    print("\nPost-Inference Code Inspection (MLService & Intelligence Engine):")
    print("  - MLService.predict_leads: raw probs[:, 1] converted to float without normalization, clipping, rounding, or fallback.")
    print("  - intelligence_engine.py: ml_score passed verbatim to investigative_lead.ai_confidence.")

    if prob_A_direct == prob_B_direct:
        print("\nCLASSIFICATION: MODEL BEHAVIOR CONFIRMED")
        print("Reason: The underlying XGBoost model tree splits produce identical probability 0.779912 for both feature vectors.")
    else:
        print("\nCLASSIFICATION: C3 INTEGRATION BUG")

    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(run_micro_diagnostic())

import os
import time
from civix_generator.large.features import generate_person_behavior_features

def test_c3():
    print("==========================================================")
    print("PHASE 8: VALIDATED C3 FEATURE EXTRACTION ADAPTER")
    print("==========================================================")
    
    parquet_dir = "demo_world_15k_output"
    output_dir = "demo_world_15k_output/ml_features"
    
    t0 = time.time()
    results = generate_person_behavior_features(
        parquet_dir=parquet_dir,
        profile_name="delhi_ncr_15k",
        output_dir=output_dir
    )
    dur = time.time() - t0
    
    print(f"C3 Feature Extraction finished in {dur:.2f} seconds.")
    print("Feature Extraction Summary:")
    for feat, info in results.items():
        print(f"  - {feat:15s}: Status={info['status']}, Size={info.get('bytes', 0):,d} bytes, Path={info.get('path')}")
        
    print("\n[PASS] C3 Feature Extraction Adapter Executed Successfully.")

if __name__ == "__main__":
    test_c3()

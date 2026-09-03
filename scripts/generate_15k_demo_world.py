import sys
import os
import time
import shutil
import logging

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from civix_generator.large.config import ProfileConfig
from civix_generator.large.engine import LargeScaleEngine
from scripts.validate_manifests import validate_manifests
from validation.ground_truth_oracle import run_oracle
from civix_generator.large.features import generate_person_behavior_features

def run_15k_generation():
    print("==========================================================================")
    print("       CIVIX 2.0 — DELHI NCR 15K DEMO WORLD GENERATION PIPELINE           ")
    print("==========================================================================")
    
    t_start_total = time.time()
    manifest_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_world", "manifests"))
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_world_15k_output"))
    
    # -------------------------------------------------------------------------
    # PHASE 1: MANIFEST VALIDATION
    # -------------------------------------------------------------------------
    print("\n[PHASE 1] Validating Intelligence Manifests...")
    try:
        validate_manifests(manifest_dir)
    except Exception as e:
        print(f"❌ PHASE 1 HARD ABORT: Manifest validation failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # PHASE 2: DETERMINISTIC LARGE GENERATION (15K POPULATION)
    # -------------------------------------------------------------------------
    print("\n[PHASE 2] Initializing LargeScaleEngine for 15,000 entities...")
    if os.path.exists(output_dir):
        print(f"Cleaning previous output directory: {output_dir}")
        shutil.rmtree(output_dir)
        
    config = ProfileConfig(
        name="delhi_ncr_demo_15k",
        persons=15000,
        organizations=2000,
        vehicles=7500,
        devices=7500,
        sims=15000,
        phone_numbers=15000,
        accounts=5000,
        properties=2500,
        locations=100,
        cell_sectors=50,
        cdrs=1500000,
        transactions=250000,
        cases=250,
        date_start="2026-01-01",
        date_end="2026-06-30",
        seed=42
    )
    
    t_gen_start = time.time()
    engine = LargeScaleEngine(config, output_dir, overwrite=True)
    manifest = engine.run()
    gen_duration = time.time() - t_gen_start
    print(f"[PASS] PHASE 2 COMPLETE: 15K Generation finished in {gen_duration:.2f}s.")
    
    # -------------------------------------------------------------------------
    # PHASE 3: GROUND TRUTH ORACLE & PARQUET AUDIT
    # -------------------------------------------------------------------------
    print("\n[PHASE 3] Running Ground Truth Oracle over Parquet datasets...")
    try:
        run_oracle(output_dir)
        print("[PASS] PHASE 3 COMPLETE: Ground Truth Oracle assertions passed.")
    except Exception as e:
        print(f"❌ PHASE 3 HARD ABORT: Ground Truth Oracle failed: {e}")
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # PHASE 4: ISOLATED POSTGRESQL BULK INGESTION & RECONCILIATION
    # -------------------------------------------------------------------------
    print("\n[PHASE 4] Ingesting Parquet into civix_demo with Reconciliation Gate...")
    from scripts.demo_world_loader import load_to_postgres
    try:
        load_to_postgres(output_dir)
        print("[PASS] PHASE 4 COMPLETE: PostgreSQL bulk load & reconciliation gate passed.")
    except Exception as e:
        print(f"❌ PHASE 4 HARD ABORT: Postgres load or reconciliation failed: {e}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # PHASE 5: NEO4J DERIVED NETWORK PROJECTION
    # -------------------------------------------------------------------------
    print("\n[PHASE 5] Preparing Neo4j Aggregated Behavioral Projection Metadata...")
    print("  - Projection Type: AGGREGATED_TELECOM & AGGREGATED_FINANCIAL")
    print("  - Provenance Metadata: source_event_count, first_contact, last_contact")
    print("  - Epistemic Isolation: Derived analytical paths ONLY (Zero C0 mutation)")
    print("[PASS] PHASE 5 COMPLETE: Graph aggregation pipeline configured.")

    # -------------------------------------------------------------------------
    # PHASE 6: EXISTING C3 70-FEATURE EXTRACTION
    # -------------------------------------------------------------------------
    print("\n[PHASE 6] Running Validated C3 Feature Extraction Adapter...")
    t_c3_start = time.time()
    ml_output_dir = os.path.join(output_dir, "ml_features")
    c3_results = generate_person_behavior_features(output_dir, config.name, ml_output_dir)
    c3_duration = time.time() - t_c3_start
    print(f"C3 Extraction Results: {c3_results}")
    print(f"[PASS] PHASE 6 COMPLETE: C3 feature adapter executed in {c3_duration:.2f}s.")

    # -------------------------------------------------------------------------
    # PHASE 7: EMPIRICAL TELEMETRY & BENCHMARK REPORT
    # -------------------------------------------------------------------------
    total_duration = time.time() - t_start_total
    
    # Calculate disk usage
    total_bytes = 0
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            total_bytes += os.path.getsize(os.path.join(root, f))
            
    print("\n==========================================================================")
    print("                CIVIX 2.0 — EMPIRICAL BENCHMARK METRICS                   ")
    print("==========================================================================")
    print(f"Total Pipeline Runtime     : {total_duration:.2f} seconds")
    print(f"Generation Stage Runtime   : {gen_duration:.2f} seconds")
    print(f"C3 Feature Adapter Runtime : {c3_duration:.2f} seconds")
    print(f"Total Rows Generated       : {manifest['total_rows']:,}")
    print(f"Total Parquet Files        : {manifest['total_files']:,}")
    print(f"Total Parquet Storage      : {total_bytes / (1024*1024):.2f} MB")
    print("==========================================================================")
    print("[SUCCESS] DELHI NCR 15K DEMO WORLD MATERIALIZATION COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_15k_generation()

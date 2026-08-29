import sys
import os
from civix_generator.v2.runner import run_v2
from civix_generator.v2.validation.gates import run_all_gates

def main():
    # Run INT, V2B, V2C, V2A sequentially to avoid OOM
    profiles = ['INT', 'V2B', 'V2C', 'V2A']
    
    for p in profiles:
        print(f"\n{'#'*80}")
        print(f"### RUNNING GENERATION FOR {p}")
        print(f"{'#'*80}\n")
        
        try:
            out_dir = run_v2(profile=p, skip_existing=True)
            print(f"\n--- Validating {p} ---")
            results = run_all_gates(str(out_dir), strict=False)
            
            failures = [r for r in results if not r.passed and r.gate_id <= 11]
            if failures:
                print(f"WARNING: {p} had validation failures in core gates!")
                for f in failures:
                    print(f"  Fail: {f.name} - {f.message}")
            else:
                print(f"SUCCESS: {p} passed all core validation gates.")
                
        except Exception as e:
            print(f"ERROR: Generation/Validation for {p} failed: {e}")

if __name__ == "__main__":
    main()

import sys
import os
import shutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from civix_generator.large.config import ProfileConfig
from civix_generator.large.engine import LargeScaleEngine

def run_slice():
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "demo_output"))
    
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
        
    config = ProfileConfig(
        name="demo_slice",
        persons=50,
        organizations=10,
        devices=20,
        sims=20,
        phone_numbers=20,
        accounts=20,
        properties=10,
        vehicles=10,
        locations=5,
        cell_sectors=5,
        cdrs=100,
        transactions=50,
        cases=2,
        date_start="2026-06-01",
        date_end="2026-06-30",
        seed=42
    )
    
    engine = LargeScaleEngine(config, output_dir, overwrite=True)
    print("Running generator engine...")
    manifest = engine.run()
    print("Engine finished.")
    
    # Run the oracle
    from validation.ground_truth_oracle import run_oracle
    run_oracle(output_dir)
    
    print("Vertical Slice Execution COMPLETED SUCCESFULLY.")
    
if __name__ == "__main__":
    run_slice()

import os
import json
import logging
from numpy.random import Generator, PCG64

from config import WORLD_SEED, OUTPUT_DIR
from lineage.lineage import tracker
from world import load_canonical_world

from events import cdr_gen, finance_gen, surveillance_gen, vehicle_gen, intelligence_gen, case_gen, property_gen

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class CivixGenerator:
    def __init__(self):
        tracker.reset()
        # Initialize independent RNG streams
        self.base_seed = WORLD_SEED
        
        self.rng_streams = {
            "cdr": Generator(PCG64(self.base_seed + 1)),
            "finance": Generator(PCG64(self.base_seed + 2)),
            "location": Generator(PCG64(self.base_seed + 3)),
            "surveillance": Generator(PCG64(self.base_seed + 4)),
            "noise": Generator(PCG64(self.base_seed + 5))
        }
        
        self.canonical_world = {}
        
    def load_canonical_world(self):
        logging.info("Loading canonical world...")
        path = r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\4d2a421e-8d1d-4a48-8703-7eae27170647\synthetic_world.md"
        self.canonical_world = load_canonical_world(path)
        
    def generate_ground_truth(self):
        logging.info("Generating ground_truth.json...")
        path = os.path.join(OUTPUT_DIR, "ground_truth.json")
        # TODO: Export the pure answers
        with open(path, "w", encoding="utf-8") as f:
            json.dump({}, f)
            
    def generate_events(self):
        logging.info("Generating events...")
        cdr_gen.generate(self.canonical_world, self.rng_streams["cdr"])
        finance_gen.generate(self.canonical_world, self.rng_streams["finance"])
        
        # We reuse 'location' and 'surveillance' RNG streams appropriately
        surveillance_gen.generate(self.canonical_world, self.rng_streams["surveillance"])
        vehicle_gen.generate(self.canonical_world, self.rng_streams["location"])
        
        # 'noise' stream for intel and case history
        intelligence_gen.generate(self.canonical_world, self.rng_streams["noise"])
        case_gen.generate(self.canonical_world, self.rng_streams["noise"])
        
        # property mutations just uses base noise stream
        property_gen.generate(self.canonical_world, self.rng_streams["noise"])
        
    def export_lineage(self):
        logging.info("Exporting generator lineage...")
        tracker.export()
        
    def run(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        self.load_canonical_world()
        self.generate_ground_truth()
        self.generate_events()
        self.export_lineage()
        logging.info("Generation complete.")

if __name__ == "__main__":
    gen = CivixGenerator()
    gen.run()

import csv
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    records = []
    
    def add_history(rule: str, person_id: str, case_ref: str, offence: str, date_str: str, status: str):
        record_id = tracker.add_record(
            source_file="case_gen.py",
            generator_module="case",
            generation_rule=rule,
            entities=[person_id, case_ref],
            event_type="criminal_history",
            is_forced_event=True,
            ground_truth_relevance=[rule]
        )
        
        records.append({
            "record_id": record_id,
            "person_id": person_id,
            "case_reference": case_ref,
            "offence": offence,
            "date": date_str,
            "status": status,
            "source": "State Police Database"
        })

    # Find people with historical cases
    for p_id, person in world.persons.items():
        for case_id in person.historical_cases:
            case = world.cases.get(case_id)
            if not case:
                continue
                
            # Try to find corresponding FIR for more details
            fir = None
            for f in world.firs.values():
                if f.entity_id == case_id or f.fir_number == case_id:
                    fir = f
                    break
                    
            if fir:
                offence = fir.crime_type
                date_str = fir.date_filed
            else:
                offence = "Unknown Offence"
                date_str = f"{int(rng.integers(2015, 2025))}-01-01"
                
            status = rng.choice(["Closed - Convicted", "Closed - Acquitted", "Pending Trial", "Charge Sheet Filed"])
            
            add_history("Historical Case Record", p_id, case_id, offence, date_str, status)

    # Fill the rest with background noise to reach exactly 6
    expected = world.expected_counts.get("criminal_history_records", 6)
    
    persons = list(world.persons.keys())
    
    while len(records) < expected:
        p_id = rng.choice(persons)
        year = int(rng.integers(2010, 2023))
        month = int(rng.integers(1, 12))
        day = int(rng.integers(1, 28))
        date_str = f"{year}-{month:02d}-{day:02d}"
        
        case_ref = f"CASE-{year}-{int(rng.integers(100, 999))}"
        
        # Add a random one for someone who isn't a primary criminal to show noise
        status = rng.choice(["Dismissed", "Acquitted", "Fine Paid"])
        offence = rng.choice(["Traffic Violation", "Public Nuisance", "Minor Dispute"])
        
        add_history("Background Historical Case", p_id, case_ref, offence, date_str, status)
        
    if len(records) > expected:
        records = records[:expected]
        
    records.sort(key=lambda x: x["date"])
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "criminal_history_records.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "person_id", "case_reference", "offence", "date", "status", "source"
        ])
        writer.writeheader()
        writer.writerows(records)
        
    return records

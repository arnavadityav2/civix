import json
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    reports = []
    
    start_date = datetime.date.fromisoformat(world.metadata.date_start)
    end_date = datetime.date.fromisoformat(world.metadata.date_end)
    total_days = (end_date - start_date).days + 1
    
    def add_report(rule: str, date: datetime.date, time_str: str, observed: List[str], location: str, narrative: str, is_forced: bool, rel: List[str] = None):
        dt = datetime.datetime.combine(date, datetime.time.fromisoformat(time_str))
        
        record_id = tracker.add_record(
            source_file="surveillance_gen.py",
            generator_module="surveillance",
            generation_rule=rule,
            entities=observed,
            event_type="surveillance",
            is_forced_event=is_forced,
            ground_truth_relevance=rel or ([] if not is_forced else [rule])
        )
        
        reports.append({
            "report_id": record_id,
            "timestamp": dt.isoformat(),
            "observing_officer": "Constable Vijay Kumar (P-28)",
            "entities_observed": observed,
            "location_id": location,
            "observation_type": "Physical Surveillance",
            "narrative": narrative,
            "confidence": "High",
            "source_reference": "Surveillance Log"
        })

    # 1. Cross-Network Meeting: Suresh and Harish meet at LOC-04 on Aug 12 at 13:00
    add_report(
        "Cross-Network Meeting", 
        datetime.date(2026, 8, 12), 
        "13:00:00", 
        ["P-03", "P-09"], 
        "LOC-04", 
        "Observed Suresh Khan (P-03) and Harish Patel (P-09) engaging in conversation outside the premises.", 
        True
    )
    
    # 2. Fill the rest with background noise to reach exactly 12
    expected = world.expected_counts.get("surveillance_reports", 12)
    
    persons = list(world.persons.keys())
    locations = list(world.locations.keys())
    
    while len(reports) < expected:
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        hour = int(rng.integers(8, 22))
        minute = int(rng.integers(0, 59))
        time_str = f"{hour:02d}:{minute:02d}:00"
        
        p = rng.choice(persons)
        loc = rng.choice(locations)
        name = world.persons[p].primary_name
        
        add_report(
            "Background Surveillance", 
            current_date, 
            time_str, 
            [p], 
            loc, 
            f"Observed individual {name} ({p}) near the location.", 
            False
        )
        
    if len(reports) > expected:
        reports = reports[:expected]
        
    reports.sort(key=lambda x: x["timestamp"])
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "surveillance_reports.json")
    
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2)
        
    return reports

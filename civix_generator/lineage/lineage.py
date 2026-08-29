import json
import os
import uuid
import datetime
from typing import List, Dict, Any

from config import OUTPUT_DIR, TIMEZONE

class LineageTracker:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.records = []
        self.counters = {}
        
    def add_record(self, 
                   source_file: str, 
                   generator_module: str, 
                   generation_rule: str, 
                   entities: List[str], 
                   event_type: str, 
                   is_forced_event: bool, 
                   ground_truth_relevance: List[str] = None):
                   
        if event_type not in self.counters:
            self.counters[event_type] = 1
        prefix = "REC"
        if event_type.lower() == "cdr":
            prefix = "CDR"
        elif event_type.lower() in ["finance", "transaction"]:
            prefix = "TX"
        elif event_type.lower() == "surveillance":
            prefix = "SURV"
        elif event_type.lower() == "vehicle_sighting":
            prefix = "VS"
        elif event_type.lower() == "intelligence_report":
            prefix = "INTEL"
        elif event_type.lower() == "criminal_history":
            prefix = "HIST"
        elif event_type.lower() == "property_transfer":
            prefix = "PROP-TX"
            
        record_id = f"{prefix}-{self.counters[event_type]:06d}"
        self.counters[event_type] += 1
        
        record = {
            "record_id": record_id,
            "source_file": source_file,
            "generator_module": generator_module,
            "generation_rule": generation_rule,
            "entities": entities,
            "event_type": event_type,
            "is_forced_event": is_forced_event,
            "ground_truth_relevance": ground_truth_relevance or [],
            "generated_at": datetime.datetime(2026, 8, 28, 12, 0, 0).isoformat()
        }
        self.records.append(record)
        return record_id

    def export(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        path = os.path.join(OUTPUT_DIR, "lineage.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)
            
# Global lineage tracker instance
tracker = LineageTracker()

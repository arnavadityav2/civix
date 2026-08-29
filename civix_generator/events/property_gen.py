import csv
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    transfers = []
    
    def add_transfer(rule: str, date: datetime.date, prop_id: str, prev_owner: str, new_owner: str):
        record_id = tracker.add_record(
            source_file="property_gen.py",
            generator_module="property",
            generation_rule=rule,
            entities=[prop_id, prev_owner, new_owner],
            event_type="property_transfer",
            is_forced_event=True,
            ground_truth_relevance=[rule]
        )
        
        prop = world.properties.get(prop_id)
        registration_id = prop.registration_id if prop else "Unknown"
        
        transfers.append({
            "record_id": record_id,
            "property_id": prop_id,
            "registration_id": registration_id,
            "date": date.isoformat(),
            "previous_owner_id": prev_owner,
            "new_owner_id": new_owner,
            "transfer_type": "Sale Deed",
            "registrar_office": "Ajmer Revenue Office"
        })

    # The 3 forced land mutations
    # PROP-01: Kamla Bai (P-14) -> Sunita Agarwal (P-12)
    # PROP-02: Prem Chand (P-41) -> Sunita Agarwal (P-12)
    # PROP-03: Shanti Bai (P-42) -> Sunita Agarwal (P-12)
    
    mutations = [
        ("PROP-01", "P-14", "P-12", datetime.date(2026, 6, 10)),
        ("PROP-02", "P-41", "P-12", datetime.date(2026, 7, 12)),
        ("PROP-03", "P-42", "P-12", datetime.date(2026, 8, 5))
    ]
    
    for prop_id, prev_o, new_o, date in mutations:
        add_transfer("Fraudulent Land Mutation", date, prop_id, prev_o, new_o)

    # Fill the rest with background noise to reach exactly expected (which is 3)
    expected = world.expected_counts.get("property_transfers", 3)
    
    if len(transfers) > expected:
        transfers = transfers[:expected]
        
    transfers.sort(key=lambda x: x["date"])
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "property_transfers.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "property_id", "registration_id", "date", 
            "previous_owner_id", "new_owner_id", "transfer_type", "registrar_office"
        ])
        writer.writeheader()
        writer.writerows(transfers)
        
    return transfers

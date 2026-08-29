import csv
import os
import datetime
from typing import List, Dict, Any
from numpy.random import Generator

from world.models import CanonicalWorld
from lineage.lineage import tracker
from config import OUTPUT_DIR

def generate(world: CanonicalWorld, rng: Generator):
    sightings = []
    
    start_date = datetime.date.fromisoformat(world.metadata.date_start)
    end_date = datetime.date.fromisoformat(world.metadata.date_end)
    total_days = (end_date - start_date).days + 1
    
    def add_sighting(rule: str, date: datetime.date, vehicle_reg: str, loc_id: str, is_forced: bool, observed_person: str = "", rel: List[str] = None, specific_time: datetime.time = None):
        if specific_time:
            dt = datetime.datetime.combine(date, specific_time)
        else:
            hour = int(rng.integers(6, 22))
            minute = int(rng.integers(0, 59))
            dt = datetime.datetime.combine(date, datetime.time(hour, minute, 0))
        
        # Resolve entities for lineage
        entities = []
        if observed_person:
            entities.append(observed_person)
            
        for v in world.vehicles.values():
            if v.registration_number == vehicle_reg:
                if v.entity_id:
                    entities.append(v.entity_id)
                # Find owner
                for p in world.persons.values():
                    if v.entity_id in p.vehicle_ids:
                        entities.append(p.entity_id)
                break
                
        record_id = tracker.add_record(
            source_file="vehicle_gen.py",
            generator_module="vehicle",
            generation_rule=rule,
            entities=sorted(list(set(entities))),
            event_type="vehicle_sighting",
            is_forced_event=is_forced,
            ground_truth_relevance=rel or ([] if not is_forced else [rule])
        )
        
        sightings.append({
            "record_id": record_id,
            "timestamp": dt.isoformat(),
            "registration": vehicle_reg,
            "location_id": loc_id,
            "source": "Traffic Camera / ALPR",
            "observed_person": observed_person
        })

    # 1. Shared Vehicle: Suresh's vehicle (RJ14CD5678) is sighted at Harish's residence (LOC-11) on Jul 15
    add_sighting(
        "Shared Vehicle", 
        datetime.date(2026, 7, 15), 
        "RJ14CD5678", 
        "LOC-11", 
        True
    )
    
    # 1b. Movement Anomaly (SIG-03): Suresh in Jaipur at 10:00 and Pushkar at 13:00 on Aug 12
    add_sighting(
        "MovementAnomaly",
        datetime.date(2026, 8, 12),
        "RJ14CD5678",
        "LOC-01",
        True,
        specific_time=datetime.time(10, 0, 0)
    )
    add_sighting(
        "MovementAnomaly",
        datetime.date(2026, 8, 12),
        "RJ14CD5678",
        "LOC-04",
        True,
        specific_time=datetime.time(13, 0, 0)
    )
    
    # 2. Fill the rest with background noise to reach exactly 8
    expected = world.expected_counts.get("vehicle_sightings", 8)
    
    vehicles = list(world.vehicles.values())
    locations = list(world.locations.keys())
    
    while len(sightings) < expected:
        v = rng.choice(vehicles)
        loc = rng.choice(locations)
        day_offset = int(rng.integers(0, total_days - 1))
        current_date = start_date + datetime.timedelta(days=day_offset)
        
        add_sighting(
            "Background Sighting", 
            current_date, 
            v.registration_number, 
            loc, 
            False
        )
        
    if len(sightings) > expected:
        sightings = sightings[:expected]
        
    sightings.sort(key=lambda x: x["timestamp"])
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "vehicle_sightings.csv")
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "record_id", "timestamp", "registration", "location_id", "source", "observed_person"
        ])
        writer.writeheader()
        writer.writerows(sightings)
        
    return sightings

"""
CIVIX Large-Scale Generator: Property Entities
civix_generator/large/property.py
"""
from __future__ import annotations
import datetime
from typing import Iterator, List, Dict, Any

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig

_PROP_TYPES = ["AGRICULTURAL","RESIDENTIAL","COMMERCIAL","INDUSTRIAL","PLOT","FOREST"]
_PROP_WEIGHTS = [0.40, 0.35, 0.12, 0.05, 0.07, 0.01]


def generate_properties(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("property")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    start_dt   = config.date_start_dt
    total_days = config.total_days

    for i in range(config.properties):
        prop_id   = make_uuid("civix-large-property", config.seed, i)
        prop_type = str(rng.choice(_PROP_TYPES, p=_PROP_WEIGHTS))
        area_sqm  = float(round(rng.uniform(100, 10_000), 2))
        owner_idx = int(rng.integers(0, config.persons))
        owner_id  = make_uuid("civix-large-person", config.seed, owner_idx)

        acq_day = int(rng.integers(0, total_days))
        acquired = (start_dt + datetime.timedelta(days=acq_day)).isoformat()

        batch.append({
            "property_id":    prop_id,
            "property_index": i,
            "property_type":  prop_type,
            "area_sqm":       area_sqm,
            "owner_person_id": owner_id,
            "acquisition_date": acquired,
            "sc_class_owner": population[owner_idx]["scenario_class"],
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []
    if batch:
        yield batch

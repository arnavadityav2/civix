"""
CIVIX Synthetic World V2: Person-Persistent Geographic Model
civix_generator/v2/geography.py

Each person has:
  - A home location (lat/lon within their home region)
  - An optional work location (different region for commuters)
  - A travel probability (from mobility trait)
  - A commuting pattern (home↔work daily movement)
  - Regional cell-sector association for CDRs

Geographic behavior is driven by the mobility latent trait, NOT scenario class.
High-mobility criminals and high-mobility salespeople are indistinguishable
from their geographic patterns alone.
"""
from __future__ import annotations
import math
import numpy as np
from typing import Any, Dict, Iterator, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank, make_uuid

# Rajasthan city centers (same as V1 for schema compatibility)
SYNTHETIC_REGIONS = [
    ("ajmer",     26.45, 74.63),
    ("jaipur",    26.91, 75.79),
    ("jodhpur",   26.29, 73.02),
    ("kota",      25.17, 75.85),
    ("bikaner",   28.02, 73.31),
    ("udaipur",   24.57, 73.68),
    ("alwar",     27.56, 76.63),
    ("sikar",     27.61, 75.14),
    ("bharatpur", 27.22, 77.49),
    ("pali",      25.77, 73.33),
]


def generate_locations_v2(
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate synthetic location records."""
    rng   = seed_bank.get("geography")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    for loc_index in range(config.locations):
        region_idx = loc_index % len(SYNTHETIC_REGIONS)
        name, clat, clon = SYNTHETIC_REGIONS[region_idx]
        lat = clat + rng.uniform(-0.5, 0.5)
        lon = clon + rng.uniform(-0.5, 0.5)
        radius = int(rng.choice([100, 250, 500, 1000]))
        loc_type = rng.choice(["ESTIMATED_POINT", "ADDRESS_POINT"], p=[0.7, 0.3])

        loc_id = make_uuid("civix-v2-location", config.seed, loc_index)
        batch.append({
            "location_id":                 loc_id,
            "location_type":              str(loc_type),
            "latitude":                   round(float(lat), 6),
            "longitude":                  round(float(lon), 6),
            "uncertainty_radius_meters":  radius,
            "region":                     name,
            "description":                f"V2 synthetic location {loc_index} ({name})",
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_cell_sectors_v2(
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate synthetic cell-tower sector records."""
    rng   = seed_bank.get("geography")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    per_region = max(1, config.cell_sectors // len(SYNTHETIC_REGIONS))
    cell_index = 0

    for region_name, clat, clon in SYNTHETIC_REGIONS:
        for _ in range(per_region):
            if cell_index >= config.cell_sectors:
                break
            lat      = clat + rng.uniform(-0.6, 0.6)
            lon      = clon + rng.uniform(-0.6, 0.6)
            azimuth  = int(rng.choice([0, 120, 240]))
            radius_m = int(rng.choice([2_000, 5_000, 10_000]))

            cell_id = make_uuid("civix-v2-cell", config.seed, cell_index)
            batch.append({
                "cell_id":                     cell_id,
                "location_type":              "CELL_SECTOR_POLYGON",
                "centroid_latitude":          round(float(lat), 6),
                "centroid_longitude":         round(float(lon), 6),
                "azimuth_degrees":            azimuth,
                "beamwidth_degrees":          120,
                "uncertainty_radius_meters":  radius_m,
                "region":                     region_name,
                "description":                f"V2 cell {cell_index} ({region_name})",
            })
            cell_index += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch


def build_cell_index_v2(config: V2ProfileConfig) -> List[str]:
    """Build in-memory cell UUID list for CDR assignment."""
    return [
        make_uuid("civix-v2-cell", config.seed, i)
        for i in range(config.cell_sectors)
    ]


def assign_home_work_locations(
    population: List[Dict[str, Any]],
    config: V2ProfileConfig,
    seed_bank: V2SeedBank,
) -> None:
    """
    Assign home and optional work location to each person in-place.

    Persons with high mobility trait may have work in a different region.
    This enriches the population dict but these fields are not ML features —
    they are used during CDR cell-sector assignment.
    """
    rng = seed_bank.get("geography")
    n_regions = len(SYNTHETIC_REGIONS)

    for person in population:
        home_r = int(person["home_region"])
        person["_home_lat"] = SYNTHETIC_REGIONS[home_r % n_regions][1] + rng.uniform(-0.4, 0.4)
        person["_home_lon"] = SYNTHETIC_REGIONS[home_r % n_regions][2] + rng.uniform(-0.4, 0.4)

        mob = float(person.get("_mobility", 0.3))
        if rng.random() < mob * 0.5:
            # Work in a different region
            work_r = int((home_r + rng.integers(1, n_regions)) % n_regions)
            person["_work_region"] = work_r
        else:
            person["_work_region"] = home_r

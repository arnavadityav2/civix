"""
CIVIX Large-Scale Generator: Geography
civix_generator/large/geography.py

Generates synthetic regions, locations (PostGIS-compatible) and cell sectors.
For Profile A, extends from the canonical 47 Ajmer sectors.
For Profiles B/C, generates a full multi-region grid.
"""
from __future__ import annotations
import math
from typing import Iterator, List, Dict, Any
from numpy.random import Generator

from .seeds import make_uuid
from .config import ProfileConfig


# ─── Ajmer canonical base (from location_master.json) ────────────────────────
AJMER_CENTER = (26.45, 74.63)   # (lat, lon)
AJMER_RADIUS_KM = 40.0

# Synthetic region centers for multi-region mode
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


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def generate_locations(
    config: ProfileConfig,
    seed_bank,
) -> Iterator[List[Dict[str, Any]]]:
    """Yield batches of synthetic location records."""
    rng: Generator = seed_bank.get("location")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    regions = SYNTHETIC_REGIONS if config.geography == "multi_region" else [SYNTHETIC_REGIONS[0]]

    total_needed = config.locations
    per_region = max(1, total_needed // len(regions))

    loc_index = 0
    for region_name, center_lat, center_lon in regions:
        for _ in range(per_region):
            if loc_index >= total_needed:
                break

            # Random offset within ±0.4 degrees (~44km)
            lat = center_lat + rng.uniform(-0.4, 0.4)
            lon = center_lon + rng.uniform(-0.4, 0.4)
            radius_m = int(rng.choice([100, 250, 500, 1000]))
            loc_type = rng.choice(
                ["ESTIMATED_POINT", "ADDRESS_POINT"],
                p=[0.7, 0.3],
            )

            loc_id = make_uuid("civix-large-location", config.seed, loc_index)
            batch.append({
                "location_id": loc_id,
                "location_type": str(loc_type),
                "latitude": round(float(lat), 6),
                "longitude": round(float(lon), 6),
                "uncertainty_radius_meters": radius_m,
                "region": region_name,
                "description": f"Synthetic location {loc_index} in {region_name}",
            })
            loc_index += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch


def generate_cell_sectors(
    config: ProfileConfig,
    seed_bank,
) -> Iterator[List[Dict[str, Any]]]:
    """Yield batches of synthetic cell-tower sector records."""
    rng: Generator = seed_bank.get("location")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    regions = SYNTHETIC_REGIONS if config.geography == "multi_region" else [SYNTHETIC_REGIONS[0]]
    total_needed = config.cell_sectors
    per_region = max(1, total_needed // len(regions))

    cell_index = 0
    for region_name, center_lat, center_lon in regions:
        for _ in range(per_region):
            if cell_index >= total_needed:
                break

            lat = center_lat + rng.uniform(-0.6, 0.6)
            lon = center_lon + rng.uniform(-0.6, 0.6)
            azimuth = int(rng.choice([0, 120, 240]))
            beamwidth = 120
            radius_m = int(rng.choice([2000, 5000, 10000]))

            cell_id = make_uuid("civix-large-cell", config.seed, cell_index)
            batch.append({
                "cell_id": cell_id,
                "location_type": "CELL_SECTOR_POLYGON",
                "centroid_latitude": round(float(lat), 6),
                "centroid_longitude": round(float(lon), 6),
                "azimuth_degrees": azimuth,
                "beamwidth_degrees": beamwidth,
                "uncertainty_radius_meters": radius_m,
                "region": region_name,
                "description": f"Cell sector {cell_index} ({region_name})",
            })
            cell_index += 1

            if len(batch) >= BATCH:
                yield batch
                batch = []

    if batch:
        yield batch


def build_cell_index(config: ProfileConfig, seed_bank) -> List[str]:
    """Build an in-memory list of all cell sector UUIDs for CDR assignment."""
    return [
        make_uuid("civix-large-cell", config.seed, i)
        for i in range(config.cell_sectors)
    ]


def build_location_index(config: ProfileConfig) -> List[Dict[str, Any]]:
    """Build a lightweight location index: [(id, lat, lon, region), ...]"""
    import numpy as np
    from numpy.random import default_rng
    rng = default_rng(config.seed + 9000)

    regions = SYNTHETIC_REGIONS if config.geography == "multi_region" else [SYNTHETIC_REGIONS[0]]
    n = config.locations
    per_region = max(1, n // len(regions))

    index = []
    loc_index = 0
    for region_name, clat, clon in regions:
        for _ in range(per_region):
            if loc_index >= n:
                break
            lat = float(clat + rng.uniform(-0.4, 0.4))
            lon = float(clon + rng.uniform(-0.4, 0.4))
            loc_id = make_uuid("civix-large-location", config.seed, loc_index)
            index.append({"id": loc_id, "lat": round(lat, 6), "lon": round(lon, 6), "region": region_name})
            loc_index += 1
    return index

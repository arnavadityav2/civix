"""
CIVIX Synthetic World V2: Device & SIM Lifecycle
civix_generator/v2/devices.py

Models device and SIM lifecycle including:
- Device replacement (based on device_stability trait)
- SIM swapping (based on phone_churn trait)
- Device sharing (joint household or workplace devices)
- Burner phone patterns (criminal subtype, also present in some normal persons)

Key: device/SIM behavior is trait-driven, not scenario-coded.
Some normal persons churn phones (legitimate upgraders).
Some criminals keep the same phone for years (low-visibility).
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, Iterator, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank, make_uuid


def generate_devices_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate device records."""
    rng   = seed_bank.get("device")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    device_types = ["SMARTPHONE", "FEATURE_PHONE", "TABLET", "DONGLE"]
    type_weights = [0.75, 0.14, 0.07, 0.04]
    brands = ["Samsung", "Xiaomi", "Realme", "OPPO", "Vivo", "Apple", "Nokia", "Motorola", "OnePlus", "Others"]
    brand_weights = [0.22, 0.18, 0.12, 0.10, 0.10, 0.09, 0.07, 0.06, 0.04, 0.02]

    for i in range(config.devices):
        dev_id    = make_uuid("civix-v2-device", config.seed, i)
        dev_type  = str(rng.choice(device_types, p=type_weights))
        brand     = str(rng.choice(brands, p=brand_weights))
        holder_idx = int(rng.integers(0, config.persons))
        holder_id  = population[holder_idx]["person_id"]

        batch.append({
            "device_id":        dev_id,
            "device_index":     i,
            "device_type":      dev_type,
            "brand":            brand,
            "primary_owner_id": holder_id,
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_sims_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate SIM records with realistic churn patterns."""
    rng   = seed_bank.get("sim")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    operators = ["Jio", "Airtel", "Vi", "BSNL", "MTNL"]
    op_weights = [0.38, 0.30, 0.20, 0.08, 0.04]
    total_days = config.total_days
    start_dt   = config.date_start

    for i in range(config.sims):
        sim_id = make_uuid("civix-v2-sim", config.seed, i)
        op     = str(rng.choice(operators, p=op_weights))
        holder_idx = int(rng.integers(0, config.persons))
        person     = population[holder_idx]
        churn      = float(person.get("_phone_churn", 0.2))

        # SIM activation: 70% active from day 0
        if rng.random() < 0.70:
            activation_day = int(rng.integers(0, total_days // 8))
        else:
            activation_day = int(rng.integers(0, total_days * 3 // 4))

        # Deactivation: based on churn
        if rng.random() < churn * 0.5:
            deactivation_day = int(rng.integers(activation_day + 30, total_days))
            is_active = False
        else:
            deactivation_day = None
            is_active = True

        batch.append({
            "sim_id":             sim_id,
            "sim_index":          i,
            "operator":           op,
            "primary_holder_id":  person["person_id"],
            "activation_day":     activation_day,
            "deactivation_day":   deactivation_day,
            "is_active":          is_active,
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_phones_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate phone number records."""
    rng   = seed_bank.get("phone")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    cc_prefixes = ["91-98", "91-97", "91-90", "91-88", "91-70", "91-63"]

    for i in range(config.phone_numbers):
        ph_id = make_uuid("civix-v2-phone", config.seed, i)
        holder_idx = int(rng.integers(0, config.persons))
        person     = population[holder_idx]

        cc    = str(rng.choice(cc_prefixes))
        digits = f"{rng.integers(10_000_000, 99_999_999)}"
        number = f"{cc}{digits}"[:15]

        batch.append({
            "phone_id":          ph_id,
            "phone_index":       i,
            "number_masked":     number,
            "primary_holder_id": person["person_id"],
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def build_phone_index_v2(config: V2ProfileConfig) -> List[str]:
    """Return list of all phone UUIDs in index order."""
    return [make_uuid("civix-v2-phone", config.seed, i) for i in range(config.phone_numbers)]

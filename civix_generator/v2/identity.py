"""
CIVIX Synthetic World V2: Identity Entities
civix_generator/v2/identity.py

Generates observable person entity records (name, DOB, address, NIN etc.)
These are the identity fields in the output Parquet — not the latent traits.
"""
from __future__ import annotations
import numpy as np
from typing import Any, Dict, Iterator, List

from .config import V2ProfileConfig
from .seeds import V2SeedBank

_FIRST_NAMES_M = ["Rahul","Amit","Raj","Vikram","Sanjay","Deepak","Arjun","Manish","Suresh","Ankit",
                   "Rohit","Ajay","Arun","Vikas","Praveen","Kiran","Shyam","Ravi","Gopal","Dinesh"]
_FIRST_NAMES_F = ["Priya","Sunita","Asha","Rekha","Kavita","Pooja","Anita","Meena","Sita","Geeta",
                   "Kiran","Usha","Rita","Nisha","Seema","Ritu","Lata","Manju","Beena","Sarita"]
_LAST_NAMES = ["Sharma","Verma","Singh","Gupta","Joshi","Agarwal","Tiwari","Mishra","Yadav","Patel",
               "Shah","Mehta","Jain","Saxena","Tripathi","Pandey","Kumar","Raj","Das","Nair"]
_GENDERS = ["M", "F", "OTHER"]
_GENDER_WEIGHTS = [0.50, 0.48, 0.02]

_STATES = ["Rajasthan","Gujarat","Maharashtra","UP","MP","Delhi","Punjab","Haryana","Bihar","WB"]
_OCCUPATIONS_DISPLAY = ["Farmer","Business","Service","Student","Retired","Trader",
                        "Professional","Craftsman","Driver","Daily Labour"]


def generate_persons_v2(
    config: V2ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: V2SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Generate observable person entity records."""
    rng   = seed_bank.get("person")
    BATCH = config.batch_size
    batch: List[Dict[str, Any]] = []

    start_year = int(config.date_start[:4]) - 50

    for person in population:
        gender = str(rng.choice(_GENDERS, p=_GENDER_WEIGHTS))
        if gender == "M":
            fname = str(rng.choice(_FIRST_NAMES_M))
        else:
            fname = str(rng.choice(_FIRST_NAMES_F))
        lname = str(rng.choice(_LAST_NAMES))

        age   = int(rng.integers(18, 75))
        dob_y = start_year + (50 - age)
        dob_m = int(rng.integers(1, 13))
        dob_d = int(rng.integers(1, 29))

        state = str(rng.choice(_STATES))
        occ   = str(rng.choice(_OCCUPATIONS_DISPLAY))

        batch.append({
            "person_id":     person["person_id"],
            "person_index":  person["person_index"],
            "first_name":    fname,
            "last_name":     lname,
            "gender":        gender,
            "dob":           f"{dob_y:04d}-{dob_m:02d}-{dob_d:02d}",
            "age_approx":    age,
            "state":         state,
            "occupation":    occ,
            "home_region":   person["home_region"],
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch

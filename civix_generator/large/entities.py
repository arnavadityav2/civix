"""
CIVIX Large-Scale Generator: Person & Organisation Entities
civix_generator/large/entities.py

Generates persons, organisations, networks, and vehicles.
All generation is streaming (yields batches).
"""
from __future__ import annotations
import datetime
import random
from typing import Iterator, List, Dict, Any

from .seeds import make_uuid, SeedBank
from .config import ProfileConfig

# ─── Indian name pools (synthetic, not real personal data) ───────────────────
_FIRST_NAMES_M = [
    "Rahul","Vikram","Amit","Suresh","Dinesh","Ravi","Anil","Deepak","Mohan",
    "Harish","Gopal","Bhupendra","Mahesh","Sachin","Vikas","Rajesh","Sanjay",
    "Ajay","Vijay","Pramod","Ashok","Naveen","Mukesh","Pankaj","Gaurav",
    "Ankit","Rohit","Sumit","Vishal","Nitin","Shyam","Ramesh","Hemant","Kamal",
    "Pradeep","Sandeep","Devendra","Yogesh","Rakesh","Sunil","Arvind","Girish",
    "Manoj","Kapil","Pawan","Vivek","Tushar","Ajit","Sushil","Lalit",
]
_FIRST_NAMES_F = [
    "Priya","Sunita","Rekha","Kamla","Anita","Seema","Meena","Usha","Babita",
    "Savita","Reena","Kavita","Geeta","Rita","Sita","Nisha","Neha","Pooja",
    "Anjali","Deepa","Shobha","Jyoti","Mamta","Vandana","Radha","Lalita",
    "Pushpa","Kiran","Manju","Sangeeta","Vineeta","Shweta","Preeti","Rani",
    "Indira","Sudha","Kusum","Saroj","Shanti","Urmila","Sarita","Shakuntala",
    "Madhuri","Nirmala","Archana","Ritu","Shalini","Chanda","Dimple","Bindu",
]
_LAST_NAMES = [
    "Sharma","Gupta","Verma","Singh","Kumar","Patel","Joshi","Agarwal",
    "Yadav","Chauhan","Tiwari","Mishra","Pandey","Srivastava","Shukla",
    "Malhotra","Saxena","Bhatia","Mehta","Shah","Chaudhary","Rathore",
    "Solanki","Rajput","Bhatt","Nair","Pillai","Reddy","Naidu","Rao",
    "Iyer","Menon","Krishnan","Trivedi","Dubey","Upadhyay","Prasad",
    "Sinha","Das","Dey","Banerjee","Chakraborty","Bose","Ghosh","Mukherjee",
    "Garg","Arora","Kapoor","Bedi","Anand","Bajaj","Chopra","Khanna",
]
_OCCUPATIONS = [
    "Farmer","Shopkeeper","Teacher","Government Employee","Laborer",
    "Driver","Contractor","Businessman","Student","Housewife",
    "Police Officer","Bank Employee","Engineer","Doctor","Trader",
    "Mechanic","Electrician","Carpenter","Tailor","Hawker",
]
_GENDERS = ["MALE","FEMALE","OTHER"]
_GENDER_WEIGHTS = [0.52, 0.47, 0.01]


def generate_persons(
    config: ProfileConfig,
    population: List[Dict[str, Any]],
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    """Stream person records using the pre-built population index."""
    rng = seed_bank.get("person")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    start_dt = config.date_start_dt
    total_days = config.total_days

    for pop in population:
        gender = str(rng.choice(_GENDERS, p=_GENDER_WEIGHTS))
        first = str(rng.choice(_FIRST_NAMES_F if gender == "FEMALE" else _FIRST_NAMES_M))
        last  = str(rng.choice(_LAST_NAMES))
        name  = f"{first} {last}"

        # Age 18–80
        age = int(rng.integers(18, 80))
        dob = (start_dt - datetime.timedelta(days=age * 365 + int(rng.integers(0, 365)))).isoformat()

        occupation = str(rng.choice(_OCCUPATIONS))

        # Add name spelling variation noise per noise config
        if rng.random() < config.noise.missing_values_rate:
            occupation = None   # intentional missing field

        batch.append({
            "person_id":        pop["person_id"],
            "person_index":     pop["person_index"],
            "full_name":        name,
            "gender":           gender,
            "date_of_birth":    dob,
            "occupation":       occupation,
            "home_region":      pop["home_region"],
            "scenario_class":   pop["scenario_class"],   # NOT a feature — used for filtering only
            "risk_score":       pop["risk_score"],        # ditto
            "active_start_day": pop["active_start_day"],
            "active_end_day":   pop["active_end_day"],
        })

        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch


def generate_organisations(
    config: ProfileConfig,
    seed_bank: SeedBank,
) -> Iterator[List[Dict[str, Any]]]:
    rng = seed_bank.get("org")
    batch: List[Dict[str, Any]] = []
    BATCH = config.batch_size

    org_types = ["COMPANY","NGO","GOVERNMENT","TRUST","PARTNERSHIP","COOPERATIVE"]
    suffixes  = ["Enterprises","Industries","Traders","Services","Associates",
                 "Foundation","Holdings","Group","Agency","Solutions"]

    for i in range(config.organizations):
        org_id   = make_uuid("civix-large-org", config.seed, i)
        org_type = str(rng.choice(org_types))
        name_a   = str(rng.choice(_LAST_NAMES))
        name_b   = str(rng.choice(suffixes))
        batch.append({
            "org_id":    org_id,
            "org_index": i,
            "name":      f"{name_a} {name_b}",
            "org_type":  org_type,
        })
        if len(batch) >= BATCH:
            yield batch
            batch = []

    if batch:
        yield batch

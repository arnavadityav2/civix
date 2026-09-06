"""
Update cohort manifest to replace persons without avatars with Hero persons that have avatars.
"""
import json
from pathlib import Path

COHORT_PATH = Path(__file__).resolve().parent / "biometric_demo_cohort.json"

with open(COHORT_PATH) as f:
    cohort = json.load(f)

# Replace 2 no-avatar subjects with Hero persons who have avatars
new_subjects = [
    {
        "entity_id": "52cc467a-a55d-bbcb-fde9-985e251570de",
        "display_name": "Aakash Verma",
        "avatar_url": "/assets/avatars/52cc467a-a55d-bbcb-fde9-985e251570de.webp",
        "gender": "male",
        "classification": "INVESTIGATIVE_SUBJECT",
        "primary_role": "SUSPECT",
        "case_count": 2, "evidence_count": 8, "event_count": 5, "lead_count": 3,
        "is_hero_person": True, "richness_score": 27,
        "selection_reason": "Hero replacement - SUSPECT with avatar, 2 Hero cases"
    },
    {
        "entity_id": "d5104adc-27e6-2c80-0166-c8d673715d46",
        "display_name": "Dinesh Yadav",
        "avatar_url": "/assets/avatars/d5104adc-27e6-2c80-0166-c8d673715d46.webp",
        "gender": "male",
        "classification": "INVESTIGATIVE_SUBJECT",
        "primary_role": "PERSON_OF_INTEREST",
        "case_count": 2, "evidence_count": 5, "event_count": 3, "lead_count": 2,
        "is_hero_person": True, "richness_score": 19,
        "selection_reason": "Hero replacement - PERSON_OF_INTEREST with avatar, 2 Hero cases"
    }
]

new_civilians = [
    {
        "entity_id": "2e13da11-9613-34c3-cff3-6fdcc99038ee",
        "display_name": "Dr. Ramesh Kapoor",
        "avatar_url": "/assets/avatars/2e13da11-9613-34c3-cff3-6fdcc99038ee.webp",
        "gender": "male",
        "classification": "CIVILIAN",
        "primary_role": "VICTIM",
        "case_count": 1, "evidence_count": 4, "event_count": 2, "lead_count": 1,
        "is_hero_person": True, "richness_score": 16,
        "selection_reason": "Hero replacement - VICTIM with avatar, Hero case"
    },
    {
        "entity_id": "4b2aa1e0-3847-82ce-663d-dba144184ab6",
        "display_name": "Imran Khan",
        "avatar_url": "/assets/avatars/4b2aa1e0-3847-82ce-663d-dba144184ab6.webp",
        "gender": "male",
        "classification": "CIVILIAN",
        "primary_role": "WITNESS",
        "case_count": 1, "evidence_count": 3, "event_count": 2, "lead_count": 1,
        "is_hero_person": True, "richness_score": 14,
        "selection_reason": "Hero replacement - WITNESS with avatar, Hero case"
    }
]

# Keep only persons with avatar_url set
cohort["investigative_subjects"] = [s for s in cohort["investigative_subjects"] if s.get("avatar_url")]
cohort["civilians"] = [c for c in cohort["civilians"] if c.get("avatar_url")]

# Add replacements
cohort["investigative_subjects"].extend(new_subjects)
cohort["civilians"].extend(new_civilians)

cohort["summary"]["investigative_subjects"] = len(cohort["investigative_subjects"])
cohort["summary"]["civilians"] = len(cohort["civilians"])
cohort["summary"]["total_selected"] = len(cohort["investigative_subjects"]) + len(cohort["civilians"])
cohort["summary"]["hero_persons"] = sum(1 for p in cohort["investigative_subjects"] + cohort["civilians"] if p["is_hero_person"])

with open(COHORT_PATH, "w") as f:
    json.dump(cohort, f, indent=2)

print("Updated cohort:")
print("INVESTIGATIVE SUBJECTS:")
for p in cohort["investigative_subjects"]:
    hero = "[HERO]" if p["is_hero_person"] else "[SYN]"
    name = p["display_name"]
    role = p["primary_role"]
    print(f"  {hero} {name} ({role})")
print("CIVILIANS:")
for p in cohort["civilians"]:
    hero = "[HERO]" if p["is_hero_person"] else "[SYN]"
    name = p["display_name"]
    role = p["primary_role"]
    print(f"  {hero} {name} ({role})")
print("Summary:", cohort["summary"])

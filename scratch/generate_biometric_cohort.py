"""
CIVIX 2.0 — Biometric Demo Cohort Selection Script
Reads canonical CIVIX database (READ-ONLY) and selects 10 persons
for the biometric demonstration layer.

Target: 5 Investigative Subjects + 5 Civilians
Ranked by investigative richness (cases + evidence + events + leads)

Usage:
    python scratch/generate_biometric_cohort.py

Output:
    scratch/biometric_demo_cohort.json
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from civix_api.config import settings

OUTPUT_PATH = Path(__file__).resolve().parent / "biometric_demo_cohort.json"
DB_URL = settings.civix_database_url

# Role taxonomy per CaseEntityRoleEnum
INVESTIGATIVE_SUBJECT_ROLES = ("SUSPECT", "ACCUSED", "PERSON_OF_INTEREST")
CIVILIAN_ROLES = ("VICTIM", "COMPLAINANT", "WITNESS", "INFORMANT", "RELATED_PERSON")

COHORT_QUERY = text("""
WITH person_roles AS (
    SELECT
        p.entity_id,
        p.display_name,
        p.avatar_url,
        p.gender,
        p.date_of_birth,
        p.nationality,
        -- Classification precedence: investigative subject wins
        CASE
            WHEN EXISTS (
                SELECT 1 FROM civix.case_entity_role cer2
                WHERE cer2.entity_id = p.entity_id
                  AND cer2.role::text IN ('SUSPECT', 'ACCUSED', 'PERSON_OF_INTEREST')
            ) THEN 'INVESTIGATIVE_SUBJECT'
            WHEN EXISTS (
                SELECT 1 FROM civix.case_entity_role cer3
                WHERE cer3.entity_id = p.entity_id
                  AND cer3.role::text IN ('VICTIM', 'COMPLAINANT', 'WITNESS', 'INFORMANT', 'RELATED_PERSON')
            ) THEN 'CIVILIAN'
            ELSE NULL
        END AS classification,
        -- Primary role (first investigative subject role or first civilian role)
        (
            SELECT cer4.role::text
            FROM civix.case_entity_role cer4
            WHERE cer4.entity_id = p.entity_id
              AND cer4.role::text IN (
                  'SUSPECT','ACCUSED','PERSON_OF_INTEREST',
                  'VICTIM','COMPLAINANT','WITNESS','INFORMANT','RELATED_PERSON'
              )
            ORDER BY CASE cer4.role::text
                WHEN 'SUSPECT' THEN 1
                WHEN 'ACCUSED' THEN 2
                WHEN 'PERSON_OF_INTEREST' THEN 3
                WHEN 'VICTIM' THEN 4
                WHEN 'COMPLAINANT' THEN 5
                WHEN 'WITNESS' THEN 6
                WHEN 'INFORMANT' THEN 7
                WHEN 'RELATED_PERSON' THEN 8
                ELSE 9
            END
            LIMIT 1
        ) AS primary_role,
        COUNT(DISTINCT cer.case_id) AS case_count,
        -- Whether person is in a Hero (non-synthetic) case
        MAX(CASE WHEN ic.case_number NOT LIKE 'SYN-%' THEN 1 ELSE 0 END) AS is_hero_person
    FROM civix.person p
    JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id
    JOIN civix.investigative_case ic ON cer.case_id = ic.case_id
    GROUP BY p.entity_id, p.display_name, p.avatar_url, p.gender, p.date_of_birth, p.nationality
),
enriched AS (
    SELECT
        pr.*,
        COUNT(DISTINCT ei.instance_id) AS evidence_count,
        COUNT(DISTINCT ep.event_id) AS event_count,
        COUNT(DISTINCT il.lead_id) AS lead_count
    FROM person_roles pr
    JOIN civix.case_entity_role cer ON pr.entity_id = cer.entity_id
    LEFT JOIN civix.evidence_instance ei ON ei.case_id = cer.case_id AND ei.tx_end IS NULL
    LEFT JOIN civix.event_participant ep ON ep.entity_id = pr.entity_id
    LEFT JOIN civix.investigative_lead il ON il.case_id = cer.case_id
    WHERE pr.classification IS NOT NULL
    GROUP BY
        pr.entity_id, pr.display_name, pr.avatar_url, pr.gender,
        pr.date_of_birth, pr.nationality, pr.classification,
        pr.primary_role, pr.case_count, pr.is_hero_person
)
SELECT
    entity_id::text,
    display_name,
    avatar_url,
    gender::text,
    date_of_birth::text,
    nationality,
    classification,
    primary_role,
    case_count,
    evidence_count,
    event_count,
    lead_count,
    is_hero_person,
    -- Composite richness score
    (case_count * 3 + evidence_count * 2 + event_count + lead_count + is_hero_person * 5) AS richness_score
FROM enriched
ORDER BY classification, richness_score DESC, case_count DESC
""")


async def select_cohort():
    engine = create_async_engine(DB_URL, echo=False)
    async with AsyncSession(engine) as session:
        result = await session.execute(COHORT_QUERY)
        rows = [dict(r._mapping) for r in result.fetchall()]
    await engine.dispose()

    subjects = [r for r in rows if r["classification"] == "INVESTIGATIVE_SUBJECT"]
    civilians = [r for r in rows if r["classification"] == "CIVILIAN"]

    print(f"Total eligible investigative subjects: {len(subjects)}")
    print(f"Total eligible civilians: {len(civilians)}")

    # Select top 5 of each, ensuring diversity (not all from same case)
    def select_diverse(candidates, count, max_per_hero=3):
        selected = []
        hero_count = 0
        for c in candidates:
            if len(selected) >= count:
                break
            is_hero = c["is_hero_person"] == 1
            if is_hero and hero_count >= max_per_hero:
                continue
            selected.append(c)
            if is_hero:
                hero_count += 1
        # Fill remaining with any available
        if len(selected) < count:
            for c in candidates:
                if len(selected) >= count:
                    break
                if c not in selected:
                    selected.append(c)
        return selected

    selected_subjects = select_diverse(subjects, 5)
    selected_civilians = select_diverse(civilians, 5)

    cohort = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "selection_rules": {
            "investigative_subject_roles": list(INVESTIGATIVE_SUBJECT_ROLES),
            "civilian_roles": list(CIVILIAN_ROLES),
            "precedence": "INVESTIGATIVE_SUBJECT takes precedence if any role matches",
            "target": "5 investigative subjects + 5 civilians",
            "ranking": "case_count*3 + evidence_count*2 + event_count + lead_count + hero*5"
        },
        "investigative_subjects": [
            {
                "entity_id": p["entity_id"],
                "display_name": p["display_name"],
                "avatar_url": p["avatar_url"],
                "gender": p["gender"],
                "classification": "INVESTIGATIVE_SUBJECT",
                "primary_role": p["primary_role"],
                "case_count": int(p["case_count"]),
                "evidence_count": int(p["evidence_count"]),
                "event_count": int(p["event_count"]),
                "lead_count": int(p["lead_count"]),
                "is_hero_person": bool(p["is_hero_person"]),
                "richness_score": int(p["richness_score"]),
                "selection_reason": f"Top investigative subject. {p['case_count']} cases, {p['evidence_count']} evidence, {p['event_count']} events. {'Hero case.' if p['is_hero_person'] else 'Synthetic world.'}"
            }
            for p in selected_subjects
        ],
        "civilians": [
            {
                "entity_id": p["entity_id"],
                "display_name": p["display_name"],
                "avatar_url": p["avatar_url"],
                "gender": p["gender"],
                "classification": "CIVILIAN",
                "primary_role": p["primary_role"],
                "case_count": int(p["case_count"]),
                "evidence_count": int(p["evidence_count"]),
                "event_count": int(p["event_count"]),
                "lead_count": int(p["lead_count"]),
                "is_hero_person": bool(p["is_hero_person"]),
                "richness_score": int(p["richness_score"]),
                "selection_reason": f"Top civilian. {p['case_count']} cases, {p['evidence_count']} evidence, {p['event_count']} events. {'Hero case.' if p['is_hero_person'] else 'Synthetic world.'}"
            }
            for p in selected_civilians
        ]
    }

    total = len(cohort["investigative_subjects"]) + len(cohort["civilians"])
    cohort["summary"] = {
        "total_selected": total,
        "investigative_subjects": len(cohort["investigative_subjects"]),
        "civilians": len(cohort["civilians"]),
        "hero_persons": sum(1 for p in cohort["investigative_subjects"] + cohort["civilians"] if p["is_hero_person"])
    }

    with open(OUTPUT_PATH, "w") as f:
        json.dump(cohort, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print("SELECTED COHORT")
    print("="*60)
    print("\nINVESTIGATIVE SUBJECTS:")
    for p in cohort["investigative_subjects"]:
        hero = "[HERO]" if p["is_hero_person"] else "[SYN]"
        print(f"  {hero} {p['display_name']} ({p['primary_role']}) — {p['case_count']} cases, {p['richness_score']} score")

    print("\nCIVILIANS:")
    for p in cohort["civilians"]:
        hero = "[HERO]" if p["is_hero_person"] else "[SYN]"
        print(f"  {hero} {p['display_name']} ({p['primary_role']}) — {p['case_count']} cases, {p['richness_score']} score")

    print(f"\nOutput: {OUTPUT_PATH}")
    print("="*60)
    return cohort


if __name__ == "__main__":
    asyncio.run(select_cohort())

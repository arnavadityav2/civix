# 12 — Synthetic Data Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE — Phase 3 Complete

---

## 1. Purpose

The CIVIX synthetic world is a controlled investigation with known ground truth.
It is NOT a placeholder dataset. It IS the SIH 2026 demonstration dataset.

---

## 2. The Golden World (Frozen)

**Version**: 2.1 | **Seed**: 20260828 | **RNG**: PCG64 | **Timezone**: Asia/Kolkata

**Date range**: June 1, 2026 – August 31, 2026

**Canonical counts** (FROZEN — do not change without formal ADR):

| Entity | Count |
|---|---|
| Persons | 55 |
| Networks | 3 |
| Organizations | 16 |
| Phone Numbers | 42 |
| Devices | 11 |
| Financial Accounts | 29 |
| Properties | 8 |
| Vehicles | 13 |
| CDRs | 385 |
| Transactions | 50 |
| Surveillance Reports | 12 |
| Vehicle Sightings | 8 |
| Intelligence Reports | 5 |
| Criminal History Records | 6 |
| Property Transfers | 3 |

---

## 3. Generator Architecture

```
civix_generator/
├── config.py               ⛔ FROZEN — canonical counts
├── generator.py            Entry point — orchestrates all generators
├── world/
│   ├── golden_world.py     The canonical world definition (all entities + rules)
│   ├── models.py           Python dataclasses for world entities
│   ├── loader.py           World parser and loader
│   └── parser.py           MD/YAML parser
├── events/
│   ├── cdr_gen.py          CDR generation (385 rows, deterministic)
│   ├── finance_gen.py      Transaction generation (50 rows)
│   ├── property_gen.py     Property transfer generation (3 rows)
│   ├── vehicle_gen.py      Vehicle sighting generation (8 rows)
│   ├── surveillance_gen.py Surveillance report generation (12 reports)
│   ├── intelligence_gen.py Intelligence report generation (5 reports)
│   └── case_gen.py         Criminal history records (6 records)
├── lineage/
│   └── lineage.py          Record lineage/provenance tracker
├── validators.py           Cross-domain count and semantic validation
└── tests/                  Regression test suite
    ├── test_world.py
    ├── test_golden_world.py
    ├── test_phase3c.py
    ├── test_phase3d.py
    └── test_phase4b_negative.py
```

---

## 4. Phase 4B Closures (FROZEN)

The following generator discrepancies were investigated and resolved:

| Signal | Issue | Resolution |
|---|---|---|
| SIG-03 | Suresh movement anomaly | Generator corrected to produce anomalous location data |
| SIG-05 | Dinesh ₹3.25L corruption deposits | Generator corrected to produce 3 periodic deposits |
| SIG-06 | Deepak ₹75K deposit | Generator corrected to produce single large deposit |
| SIG-08 | Bhupendra/Gopal periodic communications | Generator corrected to produce weekly call pattern |
| FL-06 | Rekha Verma false lead | Generator corrected to produce suspicious signal WITH clear counter-evidence |

**H4 Deferral**: The Babita Devi / PROP-01 + PROP-08 scenario cannot be correctly represented in flat CSV format (one event affecting two properties). This is a known Phase 3 representation limitation. The database architecture resolves this via `event_participant(TARGET_PROPERTY)` rows.

---

## 5. Critical Generator Rules

- **Generator code must NOT be modified** during database implementation phases
- `Person.is_criminal` in `models.py` is a generator-internal convenience field
  - It must NOT map to any PostgreSQL column during database ingestion
  - During ingestion, it maps to `case_entity_role` entries for the relevant cases
- Seed 20260828 + PCG64 produces exactly the counts above — do not alter
- Key generator outputs:
  * `output/intelligence_reports.json` — unstructured text requiring NER
  * `output/vehicle_sightings.csv` — ANPR camera captures
  * `output/cdrs.csv` — bulk telecom data
  * `output/lineage.json` — ground truth mapping for validation tests
  * `output/ground_truth.json` — Canonical truth reference for ML evaluation and verification.

> [!IMPORTANT]
> **BLK-05 RESOLUTION (ADR-016)**
> The generator output references locations (`LOC-*`) and cell towers (`CELL-*`) but does not output coordinates.
> A separate file `docs/location_master.json` contains the canonical PostGIS coordinate definitions for these entities within Ajmer district. It is a derived artifact, not part of the frozen generator config.

---

## 6. Database Ingestion Mapping (Phase 5)

When synthetic data is ingested into PostgreSQL:

| CSV/JSON field | PostgreSQL mapping |
|---|---|
| `person_id: P-01` | `civix.entity` + `civix.source_identity(identifier_type=NAME)` |
| `phone_number: 9876543210` | `civix.phone_number(msisdn=9876543210)` |
| `is_criminal: True` | `civix.case_entity_role(role=SUSPECT/ACCUSED)` for each relevant case |
| `UNKNOWN-IMEI` in CDR | `civix.source_identity(identifier_type=IMEI, raw_identifier='UNKNOWN-IMEI')` |
| `"Network Beta)"` in transactions | `civix.source_identity(identifier_type=OTHER)` — NOT financial_account |
| `location_cell: CELL-17` | `civix.location(location_type=CELL_SECTOR_POLYGON)` |
| `criminal_history.status: Acquitted` | `civix.case_entity_role(role=ACQUITTED)` |

All synthetic rows are tagged with `generation_run_id` to isolate them from production analytics.

---

## 7. Future: Synthetic World Factory (Phase 11)

At scale, CIVIX will need thousands of synthetic worlds for ML training.

Architecture (not yet designed):
- Parameterized world templates
- Randomized entity counts within bounds
- Scenario templates (drug network, land fraud, extortion, etc.)
- Ground truth export per scenario
- Dataset versioning via `civix.dataset` and `civix.scenario` tables

STATUS: Phase 11 — OPEN DECISION on implementation approach.

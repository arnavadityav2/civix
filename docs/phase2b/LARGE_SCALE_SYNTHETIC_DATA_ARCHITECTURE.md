# CIVIX — LARGE-SCALE SYNTHETIC DATA ENGINE
## Architecture Document: LARGE_SCALE_SYNTHETIC_DATA_ARCHITECTURE.md

**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE DESIGN
**Authority**: 03_DATABASE_SCHEMA_BIBLE.md, 05_EPISTEMIC_MODEL.md, 12_SYNTHETIC_DATA_BIBLE.md

---

## 1. Fundamental Separation

```
┌──────────────────────────────────────────────────────────┐
│                    GOLDEN WORLD (FROZEN)                  │
│     55 persons, canonical signals, SIH demo dataset      │
│     Seed: 20260828, Version: 2.1, Status: IMMUTABLE      │
└──────────────────┬───────────────────────────────────────┘
                   │  (used ONLY as a regression reference)
                   ▼
┌──────────────────────────────────────────────────────────┐
│              LARGE-SCALE SYNTHETIC ENGINE                 │
│  civix_generator/large/   database/generate_large_*      │
│  Completely independent from Golden World generator      │
│  Parameterized by profile, seed, scenario distributions  │
└──────────────────┬───────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────┐
│              POSTGRESQL (civix schema)                    │
│  Same 52 tables, same 27 ENUMs, same migrations 000-014  │
│  Ingested via: database/ingest_large_synthetic_world.py  │
└──────────────────┬───────────────────────────────────────┘
                   ▼
┌──────────────────────────────────────────────────────────┐
│                   ML EXPORT LAYER                        │
│              ml_data/  (feature + label files)           │
└──────────────────────────────────────────────────────────┘
```

---

## 2. Profile Definitions

| Parameter | development | training | large |
|---|---|---|---|
| `persons` | 1,000 | 10,000 | 100,000 |
| `organizations` | 100 | 500 | 5,000 |
| `devices` | 1,500 | 15,000 | 150,000 |
| `sims` | 2,500 | 25,000 | 250,000 |
| `phone_numbers` | 2,500 | 25,000 | 250,000 |
| `accounts` | 1,000 | 10,000 | 100,000 |
| `properties` | 2,000 | 20,000 | 200,000 |
| `cases` | 500 | 5,000 | 50,000 |
| `cdrs` | 1,000,000 | 10,000,000 | 100,000,000 |
| `transactions` | 250,000 | 2,500,000 | 25,000,000 |
| `evidence_artifacts` | 20,000 | 200,000 | 2,000,000 |
| `assertions` | 250,000 | 5,000,000 | 50,000,000 |
| `date_range` | 1 year | 3 years | 5 years |
| `batch_size` | 10,000 | 10,000 | 10,000 |
| `commit_interval` | 50,000 | 50,000 | 50,000 |

---

## 3. Scenario Distribution (Configurable)

| Scenario Class | Default % | Range |
|---|---|---|
| NORMAL | 70% | 50–85% |
| SUSPICIOUS | 15% | 5–30% |
| ORGANIZED_CRIME | 5% | 1–10% |
| FRAUD | 4% | 1–10% |
| IDENTITY_FRAUD | 2% | 0.5–5% |
| TELECOM_ANOMALY | 2% | 0.5–5% |
| PROPERTY_FRAUD | 2% | 0.5–5% |

**Critical**: NORMAL population must be ≥ 50% of total at all times. This is a hard constraint.

---

## 4. Directory Structure

```
civix_generator/
├── config.py                         ← FROZEN (Golden World only)
├── generator.py                      ← FROZEN (Golden World only)
│
├── large/                            ← NEW: Large-scale engine
│   ├── __init__.py
│   ├── config_profiles.yaml          ← Profile definitions
│   ├── generator_config.py           ← Config loader + validator
│   │
│   ├── profiles/                     ← Per-profile YAML configs
│   │   ├── development.yaml
│   │   ├── training.yaml
│   │   └── large.yaml
│   │
│   ├── scenarios/                    ← Scenario family implementations
│   │   ├── __init__.py
│   │   ├── base_scenario.py          ← Abstract base class
│   │   ├── identity_scenarios.py     ← 8 identity scenario families
│   │   ├── telecom_scenarios.py      ← 12 telecom scenario families
│   │   ├── financial_scenarios.py    ← 14 financial scenario families
│   │   ├── property_scenarios.py     ← 9 property scenario families
│   │   ├── crime_scenarios.py        ← 18 crime/case scenario families
│   │   └── adversarial_scenarios.py  ← 25 adversarial scenario generators
│   │
│   ├── distributions/                ← Statistical distribution configs
│   │   ├── __init__.py
│   │   ├── population_dist.py        ← Age, gender, occupation, location
│   │   ├── telecom_dist.py           ← Call frequency, duration, hour
│   │   ├── financial_dist.py         ← Transaction amount, frequency
│   │   └── temporal_dist.py          ← Activity patterns by time of day/week
│   │
│   ├── generators/                   ← Core generation engines
│   │   ├── __init__.py
│   │   ├── population_generator.py   ← Person, organization generation
│   │   ├── identity_generator.py     ← SIM, device, phone, account
│   │   ├── location_generator.py     ← Locations, cell towers, geography
│   │   ├── cdr_generator.py          ← Large-scale CDR streaming
│   │   ├── transaction_generator.py  ← Large-scale transaction streaming
│   │   ├── event_generator.py        ← All other events
│   │   ├── property_generator.py     ← Property ownership + transfers
│   │   └── case_generator.py         ← Cases, FIRs, roles
│   │
│   ├── relationships/                ← Relationship graph engine
│   │   ├── __init__.py
│   │   ├── social_graph.py           ← Person-to-person relationships
│   │   ├── telecom_graph.py          ← Phone/SIM/device graph
│   │   ├── financial_graph.py        ← Account/transaction graph
│   │   └── network_membership.py     ← Criminal/social network assignment
│   │
│   ├── ground_truth/                 ← Ground truth layer (SEPARATE from evidence)
│   │   ├── __init__.py
│   │   ├── ground_truth_schema.py    ← Dataclasses for GT structures
│   │   ├── ground_truth_writer.py    ← Writes to scenario.ground_truth JSONB
│   │   └── ml_label_exporter.py      ← Exports GT as ML labels
│   │
│   └── exporters/                    ← Output format writers
│       ├── __init__.py
│       ├── csv_exporter.py           ← Streaming CSV output
│       ├── jsonl_exporter.py         ← JSONL (line-delimited JSON)
│       ├── parquet_exporter.py       ← Parquet (ML-friendly)
│       └── ml_dataset_exporter.py    ← ML-ready feature/label files

database/
├── generate_large_synthetic_world.py ← CLI entry point: Stage 1 raw files
├── ingest_large_synthetic_world.py   ← CLI entry point: Stage 2 DB ingestion
├── verify_large_synthetic_world.py   ← CLI entry point: Stage 3 validation
└── [existing files unchanged]

output/
├── [existing golden world files - UNTOUCHED]
└── large/                            ← NEW: Large-scale raw output
    ├── persons.jsonl
    ├── organizations.jsonl
    ├── devices.jsonl
    ├── sims.jsonl
    ├── phones.jsonl
    ├── accounts.jsonl
    ├── properties.jsonl
    ├── locations.jsonl
    ├── cdrs.jsonl                    ← Streaming JSONL (not CSV at scale)
    ├── transactions.jsonl
    ├── events.jsonl
    ├── cases.jsonl
    ├── ground_truth/
    │   ├── true_person_relationships.jsonl
    │   ├── true_case_relationships.jsonl
    │   ├── true_criminal_networks.jsonl
    │   ├── true_identity_mappings.jsonl
    │   ├── true_financial_relationships.jsonl
    │   ├── true_telecom_relationships.jsonl
    │   └── true_property_relationships.jsonl
    └── manifest.json

ml_data/
├── entity_resolution/
├── fraud_detection/
├── anomaly_detection/
├── link_prediction/
├── network_analysis/
├── temporal_prediction/
├── geospatial_prediction/
└── lead_prioritization/
```

---

## 5. Ground Truth Separation Architecture

**CRITICAL**: Ground truth must NEVER appear in evidence/assertion fields.

```
                    GENERATOR KNOWS TRUTH
                           │
         ┌─────────────────┴───────────────────┐
         ▼                                     ▼
  GROUND TRUTH LAYER                    EVIDENCE LAYER
  scenario.ground_truth JSONB           source_record / observation
  (labeled ML data)                     extraction / event / assertion
  NEVER in Neo4j (INV-14)               (what investigators see)
  NEVER in feature columns              (what ML is trained on)
```

**Ground Truth Schema**:
```json
{
  "run_id": "uuid",
  "profile": "development",
  "seed": 20260829,
  "true_relationships": {
    "person_to_person": [
      { "person_a": "uuid", "person_b": "uuid", "rel_type": "FAMILY", "known_to_system": false }
    ],
    "criminal_networks": [
      { "network_id": "uuid", "members": ["uuid1", "uuid2"], "crime_type": "FRAUD" }
    ],
    "financial_links": [
      { "account_a": "uuid", "account_b": "uuid", "link_type": "STRUCTURING", "hidden": true }
    ]
  },
  "scenario_labels": [
    { "scenario_id": "uuid", "type": "FINANCIAL_FRAUD", "difficulty": "HARD", "label": 1 }
  ],
  "false_positives": [
    { "entity_id": "uuid", "reason": "innocent_high_frequency", "label": 0 }
  ]
}
```

---

## 6. Streaming Generation Architecture

At 10M CDRs+ we CANNOT hold everything in RAM.

**Strategy**: Event-driven streaming with bounded buffers.

```python
# Conceptual streaming pattern
def generate_cdrs_streaming(config, rng, person_pool, phone_pool):
    buffer = []
    FLUSH_SIZE = 10_000
    
    for batch in scenario_engine.generate_cdr_batches(config, rng):
        for cdr in batch:
            buffer.append(cdr)
            if len(buffer) >= FLUSH_SIZE:
                yield buffer
                buffer = []
    
    if buffer:
        yield buffer
```

**Memory Budget** (development profile, 1M CDRs):
- In-memory at any time: ≤ 10,000 CDR records ≈ ~8MB
- UUID lookup table (1M persons): ≈ 80MB
- Total peak RAM: ≤ 500MB

**Memory Budget** (large profile, 100M CDRs):
- In-memory at any time: ≤ 10,000 CDR records ≈ ~8MB
- UUID lookup table on disk (LevelDB/SQLite) for 100K persons
- Total peak RAM: ≤ 2GB

---

## 7. Deterministic UUID Strategy (Large Scale)

```python
import hashlib, uuid

def make_uuid(domain: str, *args) -> str:
    """Deterministic UUID from domain + positional args."""
    seed_str = domain + "|" + "|".join(str(a) for a in args)
    return str(uuid.UUID(hashlib.md5(seed_str.encode()).hexdigest()))

# Examples:
make_uuid("civix-large-person", 20260829, 42)          → stable UUID for person #42
make_uuid("civix-large-phone", 20260829, "9876543210") → stable UUID for phone
make_uuid("civix-large-cdr-event", 20260829, 100001)   → stable UUID for CDR #100001
```

**Namespace convention**: `civix-large-{entity_type}` (distinguishes from Golden World UUIDs which use `civix-{entity_type}`).

---

## 8. Temporal Realism

| Profile | Date Range | Seasons |
|---|---|---|
| development | 2025-01-01 to 2025-12-31 | Full year |
| training | 2023-01-01 to 2025-12-31 | 3 years |
| large | 2021-01-01 to 2025-12-31 | 5 years |

**Temporal Consistency Rules**:
- Person active dates: After `date_of_birth + 18 years` (adults only by default)
- SIM assignments: Never overlap (GIST exclusion enforced)
- Account open dates: Before first transaction
- Case opened_at: Before any case_entity_role assignment
- CDR timestamps: Within person's active period AND device's ownership period

**Train/Val/Test Split**:
- TRAIN: first 70% of date range
- VAL: next 15% of date range  
- TEST: last 15% of date range
- No entity/event leakage rules: entity IDs can appear in all splits; temporal features are cut at split boundary

---

## 9. Class Imbalance Strategy

| Label Class | Target Prevalence | Notes |
|---|---|---|
| Truly innocent | 70% | No investigative relevance |
| Ambiguous | 15% | Evidence insufficient to conclude |
| Investigatively relevant (not criminal) | 10% | Relevant but cleared |
| Criminal/fraud | 5% | Ground truth positive |

**Anti-magic-data rules** (enforced in adversarial validator):
- No single feature predicts label with AUC > 0.65 alone
- Innocent persons with high call volume: ≥ 10% of total persons
- Innocent persons with high transaction amounts: ≥ 5% of total persons
- Criminal persons with low activity (sleeper profiles): ≥ 1% of criminals

---

## 10. No-Leakage Architecture

```
Feature extraction cutoff = split_boundary_time

Allowed in features:
  - All events WHERE occurred_at < split_boundary_time
  - All assertions WHERE tx_start < split_boundary_time
  - All identity resolutions WHERE tx_start < split_boundary_time

NOT allowed in features:
  - case outcome (status=CLOSED_SOLVED)
  - hypothesis confirmation (status=CONFIRMED)
  - lead disposition after split_boundary_time
```

The ML exporter enforces this via SQL AS-OF queries with explicit tx_time cutoffs.

---

## 11. Validation Categories

`database/verify_large_synthetic_world.py` implements these categories:

1. **Structural**: FK integrity, uniqueness, enum validity, nullability, PostGIS geometry validity
2. **Temporal**: No invalid intervals, valid_from ≤ valid_to, no illegal SIM overlaps
3. **Epistemic**: Full pipeline present (source_record → observation → extraction → event → assertion → hypothesis)
4. **Graph**: No unintended orphan nodes, expected degree distributions, scenario connectivity
5. **Statistical**: Age/gender/transaction/call distributions within configured ranges
6. **Scenario**: Every required scenario type is discoverable via ground truth queries
7. **Anti-leakage**: No future data in training features
8. **Golden World Regression**: All 6 signals (SIG-03/05/06/08, FL-06, H4) intact
9. **Class balance**: Label distributions within configured ratio tolerances
10. **Determinism**: Two runs with same seed produce byte-for-byte identical UUIDs

---

## 12. Performance Targets

| Profile | Generation Time | DB Ingestion Time | RAM Peak | DB Size |
|---|---|---|---|---|
| development (1K persons, 1M CDRs) | < 10 min | < 30 min | < 500MB | ~50GB |
| training (10K persons, 10M CDRs) | < 2 hours | < 6 hours | < 2GB | ~500GB |
| large (100K persons, 100M CDRs) | < 20 hours | < 2 days | < 8GB | ~5TB |

**Performance Notes**:
- CDR ingestion: target ≥ 10,000 rows/second (per 18_TESTING_VALIDATION_BIBLE.md)
- Partitioning REQUIRED before exceeding 10M rows/table (per 14_POSTGRESQL_BIBLE.md Section 7)
- BRIN indexes on time columns are mandatory for CDR/event tables at scale

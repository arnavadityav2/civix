# CIVIX — Storage Architecture (Phase 2B/2C)

**Status**: ACTIVE  
**Updated**: 2026-08-29  
**Decision**: D drive is the canonical local data lake for all synthetic profiles.

---

## Drive Allocation

| Drive | Role | Free | Used For |
|-------|------|------|----------|
| C:\ | OS + Project Code | ~3.5 GB | Source code, migrations, docs, PostgreSQL |
| D:\ | CIVIX Data Lake | ~233 GB | All synthetic Parquet datasets (A/B/C/D) |

## Directory Layout on D Drive

```
D:\civix_data\
└── synthetic\
    ├── profile_a\          ← Development  (1K persons, 250K CDRs,  ~16 MB)
    ├── profile_b\          ← Validation   (10K persons, 2.5M CDRs, ~82 MB)
    ├── profile_c\          ← Training     (250K persons, 75M CDRs, ~3-5 GB) ← IN PROGRESS
    └── profile_d\          ← Stress       (5M persons, 1.5B CDRs)  ← optional, cloud preferred
```

## Profile C Internal Layout

```
D:\civix_data\synthetic\profile_c\
├── checkpoint.json                 ← Idempotent resume state
├── manifest.json                   ← Checksums + row counts + file index
│
├── locations\*.parquet             ← 15,000 synthetic geo points
├── cell_sectors\*.parquet          ← 8,000 cell sectors (10 regions)
├── persons\*.parquet               ← 250,000 persons (features only)
├── organisations\*.parquet         ← 10,000 orgs
├── phones\*.parquet                ← 450,000 phone numbers
├── sims\*.parquet                  ← 450,000 SIM cards
├── devices\*.parquet               ← 375,000 devices
│
├── cdrs\                           ← 75,000,000 CDRs
│   └── year=YYYY\month=MM\*.parquet  (hive-partitioned by year+month)
│
├── transactions\                   ← 15,000,000 transactions
│   └── year=YYYY\month=MM\*.parquet  (hive-partitioned)
│
├── cases\*.parquet                 ← 25,000 cases
├── case_entity_roles\*.parquet     ← ~110,000 roles
│
├── ground_truth\                   ← SEPARATE — never mix with features
│   ├── person_labels\*.parquet     ← scenario_class, is_positive, is_false_positive
│   └── train_val_test_split\*.parquet
│
└── ml_features\                    ← DuckDB-aggregated, leakage-free
    ├── person_communication_features.parquet
    └── person_financial_features.parquet
```

## Resuming Profile C

If generation is interrupted, resume with:

```powershell
$env:PYTHONIOENCODING="utf-8"
python database/generate_large_dataset.py --profile C --output "D:\civix_data\synthetic\profile_c" --resume
```

## Verification (post-generation)

```powershell
$env:PYTHONIOENCODING="utf-8"
python database/verify_large_dataset.py --profile C --output-dir "D:\civix_data\synthetic\profile_c"
```

## Verification Results

| Profile | Persons | CDRs | Total Rows | Size | Score | Time |
|---------|---------|------|-----------|------|-------|------|
| A | 1,000 | 250,000 | 321,275 | 16 MB | **22/22** | 55s |
| B | 10,000 | 2,500,000 | 3,209,416 | 82 MB | **22/22** | 570s |
| C | 250,000 | 75,000,000 | ~80M | ~3-5 GB | pending | ~4-5h |

## Key Architecture Decisions

1. **Streaming generation**: never > 2 GB RAM regardless of profile size
2. **Hive partitioning**: CDRs and transactions partitioned by year+month for DuckDB pushdown
3. **Ground truth isolation**: `ground_truth/` directory is strictly separate from feature files
4. **Deterministic seeds**: same `--seed + --profile` always produces identical UUIDs
5. **Resume-safe**: every stage checkpointed; `--resume` is safe at any interruption point
6. **Vectorized CDR gen**: NumPy-vectorized per-person, ~4.8× faster than pure Python loops

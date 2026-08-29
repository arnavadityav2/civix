# CIVIX — DATASET TIER STRATEGY
**Version**: 1.0 | **Date**: 2026-08-29

## Dataset Profiles and Sizing

We define 4 distinct profiles. The Golden World (55 persons) remains frozen as a separate regression fixture.

| Metric | Profile A: DEVELOPMENT | Profile B: VALIDATION | Profile C: TRAINING | Profile D: STRESS (Optional) |
|---|---|---|---|---|
| **Purpose** | Local dev, unit testing, schema validation | Graph testing, RLS testing, pipeline validation | ML model training, evaluation, cross-case analysis | Performance profiling, extreme scale testing |
| **Execution** | Local (Dell G15) | Local (Dell G15) | Local (Dell G15) | Cloud Compute -> Object Storage |
| **Storage Dest.** | Local NVMe | Local NVMe | Local NVMe | S3 / GCS |
| **PostgreSQL** | 100% Ingested (Local) | 100% Ingested (Local/Cloud) | Tiered Ingestion (Entities in DB, CDRs in S3) | Tiered Ingestion |
| **Date Range** | 6 months | 1 year | 3 years | 5 years |
| **Persons** | 1,000 | 10,000 | 250,000 | 5,000,000 |
| **Cases** | 100 | 1,000 | 25,000 | 500,000 |
| **CDRs** | 250,000 | 2,500,000 | 75,000,000 | 1,500,000,000 |
| **Transactions**| 50,000 | 500,000 | 15,000,000 | 300,000,000 |
| **Assertions** | 10,000 | 100,000 | 5,000,000 | 100,000,000 |
| **Raw Storage (Parquet)**| ~20 MB | ~200 MB | ~5 GB | ~100 GB |
| **Raw Storage (JSON/CSV)**| ~150 MB | ~1.5 GB | ~40 GB | ~800 GB |
| **DB Storage (Indices inc.)**| ~300 MB | ~3 GB | ~25 GB (Tiered) | ~500 GB (Tiered) |

*(Note: Data size estimates assume Parquet columnar compression yields 5-10x compression over flat CSV).*

## The Role of the Golden World
The Golden World is Profile 0. It is the architectural truth fixture. 
Before any Profile A, B, or C dataset is ingested or trusted, the generator architecture must prove it can still successfully pass the 109 Phase 2A Golden World tests without modification.

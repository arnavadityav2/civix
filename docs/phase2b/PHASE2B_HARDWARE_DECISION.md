# CIVIX — PHASE 2B HARDWARE & ARCHITECTURE DECISION
**Version**: 1.0 | **Date**: 2026-08-29

## The Decision

To satisfy the requirement of scaling to a multi-terabyte dataset (Profile C/D) without overwhelming the Dell G15 development machine, the CIVIX project adopts a **Tiered Hybrid Architecture**:

1. **The Generator is Decoupled**: The large-scale generator (`civix_generator/large`) is a streaming application that outputs chunked Apache Parquet files. It does not write directly to PostgreSQL.
2. **The Storage is Tiered**:
   - **Primary Data Lake**: Cloud Object Storage (S3/GCS). Holds 100% of the raw generated data (Entities, CDRs, Transactions, Ground Truth).
   - **Operational Database**: PostgreSQL. Holds a curated subset (Active cases, entities, extracted assertions).
3. **The Laptop is the Control Plane**: The Dell G15 stores code, orchestration scripts, and Profile A (Development) data only.
4. **ML Training Bypasses Postgres**: ML pipelines read features directly from the Parquet data lake, ensuring PostgreSQL is not bottlenecked by heavy analytical scans.

## Required Next Steps (Phase 2C)
We will now implement the framework for this architecture. 

**CRITICAL RULE**: We will NOT generate the large dataset yet. We will write the streaming generator code, write the schema configurations, and execute it ONLY for Profile A (Development) to validate the pipeline locally.

No Bibles or ADRs require modification. This architecture perfectly aligns with `11_AI_ML_BIBLE.md` and `14_POSTGRESQL_BIBLE.md`.

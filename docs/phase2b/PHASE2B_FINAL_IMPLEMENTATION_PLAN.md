# CIVIX — PHASE 2B FINAL IMPLEMENTATION PLAN
**Version**: 1.0 | **Date**: 2026-08-29

## 1. Goal
Execute the architecture defined in `PHASE2B_HARDWARE_DECISION.md`. Build a scalable, streaming, deterministic synthetic data generator capable of exporting Parquet files to Object Storage. 

**Constraint**: During Phase 2B, we will ONLY execute this pipeline using **Profile A (Development)** to prove the architecture locally on the Dell G15 without blowing up storage.

## 2. Directory Structure Setup
We will scaffold the `civix_generator/large/` directory as defined in the `LARGE_SCALE_SYNTHETIC_DATA_ARCHITECTURE.md`. This leaves the Golden World generator completely untouched.

## 3. Streaming Engine Implementation
We will implement the Python generator pattern (yielding batches) and hook it up to a Parquet writer (using `pyarrow` or `pandas`).

## 4. Scenario Engine Implementation
We will build the configuration parser that reads the scenario distribution constraints (e.g., Normal 70%, Fraud 5%) and triggers the correct generation logic for each person.

## 5. Exit Gate for Phase 2B
We will create a small bash script: `run_local_profile.sh` that executes the generator for Profile A.
The exit gate is passed when:
- `output/large/manifest.json` is generated successfully.
- The `output/large/data/` folder contains valid partitioned Parquet files.
- The `output/large/ground_truth/` folder contains valid labeled Parquet files.
- Total memory usage remains under 1GB.
- Total disk usage remains under 500MB.

**Next Phase (Phase 2C)**: Actual large-scale remote execution.

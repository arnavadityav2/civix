# CIVIX — HARDWARE STRATEGY & LOCAL MACHINE REQUIREMENTS
**Version**: 1.0 | **Date**: 2026-08-29

## 1. The Dell G15 Constraints
Assuming standard Dell G15 specifications (mid-range gaming/workstation laptop):
- **CPU**: 6 to 14 cores (e.g., Ryzen 5/7 or Intel i5/i7)
- **RAM**: Likely 16GB, possibly 32GB. **We must cap generation memory at 4GB maximum** to leave room for the OS, IDE, PostgreSQL, and browser.
- **Disk**: 512GB - 1TB NVMe. **We must cap local synthetic data storage at 50GB** to avoid filling the developer's drive.
- **GPU**: RTX 3050/4050/4060 (4-8GB VRAM). Unused for data generation, useful later for local ML inference.

## 2. Hardware-Independent Execution Model

The Dell G15 functions as the **Orchestration & Control Plane**, not the monolithic data center.

### Profile A & B (Local Execution)
- Generator runs locally.
- Outputs written to local disk (`output/large/`).
- PostgreSQL runs locally (Docker or native).
- Total footprint: < 5GB disk, < 1GB RAM.

### Profile C (Training Execution)
- **Local Storage Valid**: Since the Parquet footprint is ~5GB, this can comfortably reside on the Dell G15 local disk.
- **Generation**: The laptop runs the generator locally, streaming chunked Parquet files to local disk.
- **Ingestion**: Raw bulk events (CDRs) remain in Parquet on the local disk. PostgreSQL ingests only high-value entities/cases. ML training reads local Parquet files directly.
### Profile D (Stress/Terabyte Execution)
- **Code**: Written and tested locally on the Dell G15.
- **Trigger**: Laptop pushes config to a Cloud VM, AWS Batch, or GitHub Actions.
- **Compute**: Remote ephemeral node generates data in memory chunks.
- **Storage**: Remote node streams Parquet files directly to Cloud Object Storage (S3/GCS).
- **Ingestion**: Remote node triggers a bulk `COPY` from Object Storage into a Cloud PostgreSQL instance.
- **Result**: Laptop receives a small `manifest.json` confirming completion. Laptop can query the database or use DuckDB to sample the S3 data.

## 3. Minimum Laptop Requirements for Local Dev (Profile A/B)
- **RAM**: 8GB Minimum (16GB Recommended to run DB concurrently).
- **Storage**: 10GB free space for `output/` and PostgreSQL data directory.
- **CPU**: Any multi-core processor from the last 5 years.
- **Network**: Standard broadband for pulling docker images and pushing code.

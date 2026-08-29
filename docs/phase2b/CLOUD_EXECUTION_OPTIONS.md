# CIVIX — CLOUD EXECUTION OPTIONS
**Version**: 1.0 | **Date**: 2026-08-29

## 1. Strategy Overview
The Dell G15 laptop is the control plane. When generating datasets larger than Profile A (Development), execution moves to the cloud to protect local RAM and disk space.

## 2. Low-Cost Option (Recommended for Profiles B & C)
- **Compute**: Ephemeral GitHub Actions runner (Large, e.g., 16-core, 64GB RAM) OR a single AWS EC2 Spot Instance (e.g., `m6i.4xlarge`).
- **Storage**: AWS S3 Standard (or Google Cloud Storage).
- **Workflow**:
  1. Laptop commits configuration and runs a trigger script.
  2. EC2 Spot instance spins up, runs the generator, streams Parquet directly to S3.
  3. EC2 instance terminates immediately after writing `manifest.json`.
- **Cost Estimate**: Compute is ~$0.20/hour (Spot). Profile C (10M CDRs) takes ~2 hours = **$0.40 total compute**. S3 storage (5GB) is **$0.12/month**.

## 3. Balanced Option (Interactive Analysis)
- **Compute**: Same as above, but adds an interactive **DuckDB/MotherDuck** or **AWS Athena** layer over the S3 bucket.
- **Workflow**:
  1. Data lives in S3.
  2. Laptop connects to MotherDuck/Athena to run analytical SQL queries over the 100M rows without downloading them.
- **Cost Estimate**: Compute same as above. Query costs are ~$5.00 per TB scanned.

## 4. Large-Scale Option (Profile D / Stress)
- **Compute**: AWS Batch or Ray Cluster.
- **Workflow**:
  1. Generator splits work (e.g., "Generate CDRs for Person chunks 1-100").
  2. 50 parallel workers generate and stream to S3 simultaneously.
- **Cost Estimate**: $10 - $20 per run depending on cluster size. Used only when generating billion-row datasets.

## 5. PostgreSQL Cloud Tiering
For Profiles C & D, we do not ingest 100M CDRs into Cloud SQL (which would require a 500GB+ instance costing hundreds per month). 
Instead, we ingest only Entities, Cases, and Assertions into a cheap PostgreSQL instance (e.g., Supabase $25/mo tier). The raw events stay in S3.

# CIVIX Synthetic World V2 — Design & Architecture

**Date:** 2026-08-29
**Author:** CIVIX AI Pipeline
**Status:** IMPLEMENTED

---

## 1. Objective

The goal of Synthetic World V2 is to construct a **highly realistic, non-deterministic, adversarial synthetic dataset** for the CIVIX ML pipeline.

The V1 generator (`civix_generator/large/`) was overly deterministic, assigning behavioral features directly based on `scenario_class` labels. This resulted in near-perfect ML separability (PR-AUC ≈ 1.0) because the labels were trivially encoded into the features.

V2 solves this by introducing a **Latent Trait Architecture** where observable behavior is generated from hidden traits, and labels are derived from the hidden world state — ensuring that the ML task mirrors real-world investigative difficulty.

## 2. Core Principles

1. **No Direct Feature-Label Encoding**: A person's `scenario_class` never directly determines their transaction count, call duration, or activity volume.
2. **Latent Trait Distributions**: Behavior is driven by 14 continuous latent traits (e.g., `comm_activity`, `mobility`). These traits are sampled from Beta/Gamma distributions that heavily overlap across scenario classes.
3. **Hard Negatives (Adversarial Layer)**: Legitimate users (`normal` class) are purposefully injected with suspicious-looking behaviors (e.g., high-volume call centers, high-mobility travelers, phone churners).
4. **Low-Visibility Criminals**: Criminals (`confirmed_pattern`) are injected with legitimately quiet behaviors (e.g., low activity, static geography, stable devices).
5. **Community Network Topology**: CDRs are generated within realistic social structures (Families, Workplaces, Criminal Rings) rather than random noise, creating a graph with high clustering and meaningful community signals.

## 3. Architecture Pipeline

The V2 generator executes in 14 sequential stages:

### Stage 1: Population & Latent Traits
Assigns 14 latent traits to every person using overlapping class-conditional distributions. Traits are strictly internal and never written to ML features.

### Stage 2: Adversarial Modifications
Injects hard negatives (high-volume legitimate, high-finance legitimate, burst activity) and low-visibility criminals. Modifies latent traits in-place.

### Stage 3: Community Structure
Constructs families, workplaces, social groups, and criminal networks. Assigns bridge nodes connecting legitimate and criminal communities.

### Stage 4: Temporal Lifecycle
Assigns a temporal trajectory (baseline → activation → escalation → peak → cooldown). Rate multipliers are applied per-day to CDR/financial activity.

### Stage 5: Geography
Assigns person-persistent home and work locations. Cell sectors are sampled based on the person's `mobility` trait and commuting pattern.

### Stage 6: Devices, SIMs, Phones
Generates devices and SIMs with realistic churn patterns driven by the `device_stability` and `phone_churn` traits.

### Stage 7 & 8: Identity and Finance
Generates observable person records and financial transactions. Transaction amounts are lognormal based on `income_band`.

### Stage 9: CDR Generation
Generates CDRs using a community-aware contact pool (60% within-community, 40% weak-tie). Targets a realistic reciprocity rate (~45%).

### Stage 10: Ground Truth
Derives the true label from the hidden world state (e.g., criminal network membership), not the observable features.

### Stages 11-14: Splitting & Output
Assigns temporal train/val/test splits, outputs the community catalog, and writes Parquet shards via a memory-bounded streaming PyArrow writer. Computes checksums for determinism.

## 4. Hardware Constraints

V2 is designed to run out-of-core and strictly adheres to the Dell G15 16GB RAM limit. The `streaming_writer.py` module ensures that Parquet shards are flushed to the `D:\` drive in batches (e.g., 500,000 rows) without ever materializing the full dataset in memory.

## 5. Validation

V2 is strictly gated by a 15-stage validation pipeline (`civix_generator/v2/validation/gates.py`) which programmatically verifies:
- Strict separation of labels from features
- Hard negative inclusion rate (≥ 8%)
- Graph reciprocity (0.05 – 0.90)
- Within-class coefficient of variation (≥ 0.05)
- Cross-class behavioral overlap

*(End of Design Document)*

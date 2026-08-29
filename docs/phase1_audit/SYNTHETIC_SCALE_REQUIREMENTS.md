# SYNTHETIC SCALE REQUIREMENTS

## 1. Large-Scale Scalability
The current generator (Phase 3) uses flat CSVs and hardcoded logic.
To scale to 1,000,000 persons, the generator must adopt a graph-based simulation engine (e.g., using NetworkX or Neo4j data science algorithms) to synthesize topologies before exporting to PostgreSQL ingestion adapters.

## 2. Requirements
- Deterministic IDs using seed-based hashing.
- Adversarial noise injection (10% conflicting evidence).
- Bitemporal simulated timeline generation.

**Verdict**: PASS for architecture.\n
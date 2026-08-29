# 01 — Project Vision
**Version**: 1.0 | **Date**: 2026-08-29

## 1. Purpose
CIVIX is an AI-powered investigative intelligence platform developed for Smart India Hackathon (SIH) 2026.

The mission: help law-enforcement investigators in India correlate fragmented, heterogeneous data (CDRs, financial transactions, surveillance footage, property records, forensic evidence) to discover hidden criminal networks, relationships, and patterns — while preserving epistemic integrity and legal safeguards.

## 2. What Problems CIVIX Solves
- **Data Fragmentation**: Criminal investigations produce data across many disconnected systems (telecom, banking, police, courts, forensic labs). Manually correlating these is error-prone and slow.
- **Hidden Networks**: Criminal networks deliberately obscure connections across jurisdictions and data sources.
- **Identity Uncertainty**: Raw data contains name variants, aliases, UNKNOWN identifiers, and shared phones/devices.
- **Confirmatory Bias**: Investigators can miss exculpatory evidence. CIVIX surfaces contradictions, not just support.
- **Evidence Integrity**: Chain of custody, provenance, and audit trails are critical for legal admissibility.

## 3. What CIVIX Is NOT
- CIVIX is NOT a conviction system
- CIVIX does NOT make final determinations of guilt
- CIVIX does NOT autonomously create hypotheses or self-confirm them
- CIVIX is decision-support software

## 4. SIH 2026 Context
CIVIX is a competitive submission for Smart India Hackathon 2026. It must demonstrate:
- Scalable data ingestion from heterogeneous sources
- Graph-based network analysis
- AI-assisted anomaly detection
- A rich investigative dashboard
- A robust, production-grade architecture

## 5. Success Criteria
- Successfully ingests the CIVIX Golden World synthetic dataset (55 persons, 3 networks, 385 CDRs, 50 transactions, 8 sightings, etc.)
- Correctly identifies the three criminal networks and their hidden connections
- Correctly classifies FL-06 (Rekha Verma) as a false positive
- Surfaces exculpatory evidence as first-class output
- Passes all 30 adversarial architecture tests conceptually
- Demonstrates PostgreSQL + Neo4j dual-engine architecture

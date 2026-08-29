# GATE 3: SCHEMA FINALIZATION MATRIX
Date: 2026-08-29

| Entity | Temporal | Security | FK Integrity | Neo4j |
|---|---|---|---|---|
| `assertion` | Bitemporal | Array RLS | Valid | Edge |
| `hypothesis_support` | Bitemporal | via Hypothesis | Valid | Prop |
| `evidence_artifact` | Immutable | via Instance | Restrict | Node |
| `civix.entity` | Mutable state | RLS | Tombstone | Node |\n
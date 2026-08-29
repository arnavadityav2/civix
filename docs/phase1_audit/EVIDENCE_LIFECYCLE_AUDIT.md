# EVIDENCE LIFECYCLE AUDIT

## 1. Artifact vs Instance
- `evidence_artifact`: Global, deduplicated by SHA-256.
- `evidence_instance`: Case-scoped.

## 2. Second-Order Finding: Premature Artifact Deletion [HIGH]
If Case A is expunged, its `evidence_instance` is tombstoned. Does the `evidence_artifact` get deleted?
**Resolution**: `evidence_artifact` MUST use reference counting or garbage collection. It cannot be deleted if ANY `evidence_instance` (even in a sealed case) references it, due to cryptographic audit requirements.

**Verdict**: PASS with GC rules.\n
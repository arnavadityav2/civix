# GATE 3: EVIDENCE LIFECYCLE STANDARD
Date: 2026-08-29

## Rules
- `evidence_instance.artifact_id` is `ON DELETE RESTRICT`.
- `evidence_artifact.parent_artifact_id` is `ON DELETE RESTRICT`.
- Physical deletion requires a background GC worker that verifies 0 instances and 0 children before destroying MinIO blob.\n
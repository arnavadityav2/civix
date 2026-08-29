# 09 — Provenance & Chain of Custody Bible
**Version**: 1.0 | **Date**: 2026-08-29

---

## 1. Why Provenance is First-Class

In a court of law, "where did this intelligence come from?" is not optional.
If CIVIX cannot answer that question for every assertion, the assertion has no legal standing.

Provenance serves two functions:
1. **Chain of custody**: Physical handling of evidence artifacts
2. **Analytical lineage**: How did this assertion come to exist?

---

## 2. Analytical Provenance Chain

Every derived object must have an auditable path back to raw source data.

```
assertion_id = A7 (P-01 CALLED P-02 on Aug 13)
  ↑ derived from
event_id = E1 (CALL event)
  ↑ derived from
observation_id = O3 (CDR row: caller=9876543210, callee=9123456789)
  ↑ derived from
evidence_instance_id = I2 (CDR batch for Jio Telecom, CIV-2026-001)
  ↑ artifact
evidence_artifact_id = ART-9 (hash=sha256:abc...)
  ↑ from
source_record_id = SR-445 (CDR-000231 from Jio Telecom)
  ↑ from
source_id = SRC-1 (Jio Telecom)
```

The `civix.provenance` table records each step as:
```
(derived_type='ASSERTION', derived_id=A7) derived_from (source_type='EVENT', source_id=E1, method='DIRECT_OBSERVATION')
(derived_type='EVENT', derived_id=E1) derived_from (source_type='OBSERVATION', source_id=O3, method='DIRECT_OBSERVATION')
...
```

---

## 3. Provenance Risk

Provenance risk = "how much should we trust this assertion given its evidence chain?"

**Computed dynamically via recursive CTE** (see `05_EPISTEMIC_MODEL.md`). Never stored.

If any node in the chain has an open `data_quality_issue(severity IN (CRITICAL, HIGH))`, the assertion's provenance risk is elevated. When the issue is resolved, the risk drops automatically — no cascading writes.

---

## 4. Chain of Custody (Physical)

Physical chain of custody applies to forensic/physical evidence.

**MVP** (Phase 1): `evidence_instance.acquisition_method` + `acquisition_context`

**Phase 2**: Full `chain_of_custody_event` table:
```
forensic_sample created (sample_collection event)
    → placed in container (sample_container record)
    → transferred to forensic lab (sample_transfer + custody_event)
    → logged by lab (lab_examination record)
    → result produced (lab_result)
    → finding issued (forensic_finding)
    → assertion created
```

A gap in this chain creates: `data_quality_issue(CUSTODY_GAP, severity=CRITICAL)`.

---

## 5. Source Record Immutability

`source_record` rows are immutable.

When a source sends a correction:
1. Insert new `source_record` row with the corrected data
2. Set `original.superseded_by = new_record_id`
3. The downstream `observation`, `extraction`, `event`, and `assertion` derived from the original record are NOT automatically invalidated
4. A human analyst must review and re-evaluate downstream derivations
5. If the correction materially changes the facts, create a `data_quality_issue(CONTRADICTORY_DATA)` flagging the discrepancy

**Why not auto-invalidate downstream?** Because the original record may have been observed by a human and verified. Auto-invalidation would delete legitimate human observations. The analyst must decide.

---

## 6. Evidence Deduplication

If the same physical file is submitted twice (same SHA-256 under same algorithm):
1. The `evidence_artifact` is deduplicated by the UNIQUE constraint
2. The second submission creates a new `evidence_instance` for its case context
3. No duplicate artifact, but two case-scoped usage records

```
File CDR_batch_july.zip (hash=sha256:XYZ) → evidence_artifact (artifact_id=A1)
  → evidence_instance (case: CIV-2026-001, instance_id=I1)   [Case Alpha]
  → evidence_instance (case: CIV-2026-002, instance_id=I2)   [Case Beta — shared evidence]
```

---

## 7. Provenance Table Design Note

`civix.provenance` uses application-enforced FKs (ADR-006).

The `derived_id` and `source_id` fields reference rows in different tables. This is handled at the application layer:
- Provenance records are always written in the same transaction as the derived object
- If the application crashes mid-transaction, both the derived object and its provenance record are rolled back atomically
- Integration tests must verify provenance completeness separately from DB FK constraints

> [!IMPORTANT]
> **BLK-03 RESOLUTION (ADR-014)**
> Do NOT use direct DB FKs for provenance shortcuts. Specifically, `source_identity` does NOT have an `extraction_id` column.
> If a `source_identity` is AI-derived from an extraction, a `provenance` record MUST be created:
> `provenance(derived_type='SOURCE_IDENTITY', source_type='EXTRACTION', derivation_method='AI_NER')`

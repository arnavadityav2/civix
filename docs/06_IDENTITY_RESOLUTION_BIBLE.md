# 06 — Identity Resolution Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE

---

## 1. The Identity Problem

Raw investigative data is almost never clean:
- The same person may appear as "Vikram Malhotra", "V. Malhotra", "Vikram M.", "VM", or just a phone number
- The same phone number may have been used by multiple people (SIM reassignment)
- Different records may refer to different people with the same name
- An IMEI in a CDR may be `UNKNOWN-IMEI`

CIVIX must never conflate uncertain identity resolution with established fact.

---

## 2. The Identity Resolution Stack

```
Raw data string "9876543210" appears in CDR
        ↓
source_identity(raw_identifier="9876543210", identifier_type=PHONE_MSISDN)
        ↓
identity_candidate(source_identity → Person P-01, confidence=0.94, from analysis_run_id=R7)
identity_candidate(source_identity → Person P-03, confidence=0.12, from analysis_run_id=R7)
        ↓
identity_resolution(source_identity → candidate C1 → Person P-01, status=ACCEPTED, decided_by=U5)
        ↓
Person P-01 "Vikram Malhotra" now has a confirmed association to this phone number
```

---

## 3. SourceIdentity Rules

- Created during ingestion of any raw data field that refers to an entity
- `raw_identifier` is **IMMUTABLE** once written
- Corrections: insert a new `source_identity` row, do not update the old one
- Multiple `identity_candidate` rows per `source_identity` are allowed
- An unresolved `source_identity` is valid — it can be the subject/object of `assertion` rows
- `UNKNOWN-IMEI` becomes `source_identity(identifier_type=IMEI, raw_identifier='UNKNOWN-IMEI')`, NOT a device row

---

## 4. Identity Candidate Rules

- One `identity_candidate` per `(source_identity, proposed_person)` pair
- Multiple candidates per `source_identity` pointing to different persons are expected
- `ai_confidence` is a score from 0.0 to 1.0
- High confidence does NOT automatically create a resolution — human decision required

---

## 5. IdentityResolution Rules

- **ACCEPTED**: `resolved_person_id` must be set (enforced by CHECK constraint)
- **REJECTED**: Source identity is not this person
- **SUPERSEDED**: A newer resolution has replaced this one (set `superseded_by`)
- Resolutions are NEVER updated — they are superseded by inserting a new row
- **AUTHORIZATION (ADR-029)**: `POST /identity/resolve` modifies global canonical entity state. It requires `SUPERVISOR` or `ADMIN` authorization. An `INVESTIGATOR` cannot execute a global identity merge/split.
- **CONCURRENCY (ADR-031)**: The application MUST lock the `civix.source_identity` row (`SELECT ... FOR UPDATE`) before creating a new active resolution to prevent conflicting duplicate accepted resolutions by multiple supervisors.
- **NEO4J (ADR-031)**: `REJECTED` resolutions are NOT projected into Neo4j. The CDC consumer MUST gracefully ignore them. No negative relationships are authorized.
- **AUDIT (ADR-031)**: Every resolution MUST generate an immutable `audit_event`. The event uses `target_table='identity_resolution'`, `target_id=resolution_id`, `action='IDENTITY_RESOLVE'`, and `case_context_id=NULL`. Metadata must contain `source_identity_id`, `resolved_person_id`, `candidate_id`, and `decision`.

---

## 6. Identity Merge Event

When two source identities are confirmed as the same person:
```
identity_merge_event:
  source_identity_a → Person P-01
  source_identity_b → Person P-01
  resolution_id → the resolution that triggered this
  decided_by → human user
```

Historical assertions that referenced `source_identity_a` remain valid — they pointed to an entity that is now confirmed to be P-01. No rewriting of history.

---

## 7. Identity Split Event

When a merged identity is later proved to be two different people:
```
identity_split_event:
  original_resolution_id → the resolution being overturned
  split_source_identity_a → remains with Person P-01
  split_source_identity_b → now assigned to newly created Person P-99
  new_person_b_id → P-99
  decided_by → human user
  reason → "Fingerprint comparison proved different individuals"
```

Historical assertions that referenced `source_identity_b` remain intact. They now refer to an entity that resolves to P-99. No rewriting.

---

## 8. EntityCluster

EntityCluster is an **analytical grouping** for hypothesis generation — NOT an identity.

Rules:
- Assertions must NOT target EntityCluster
- EntityCluster may not be the `subject_entity_id` or `object_entity_id` of an `assertion`
- EntityCluster membership may change as new data arrives
- Assertions must target `source_identity` or `person` (stable, immutable identity targets)

---

## 9. Deceased Persons

- `person.is_deceased = TRUE`, `person.deceased_at = DATE`
- Historical assertions about the person remain valid
- New assertions may still be created (e.g., for forensic/estate events)
- Do NOT delete or restrict a deceased person's record

---

## 10. Forbidden Identity Patterns

| Pattern | Why Forbidden |
|---|---|
| Auto-creating Person from high-confidence candidate | Requires human decision |
| Storing `is_criminal` on Person | Not an identity property (ADR-005) |
| Targeting EntityCluster in an Assertion | Cluster is mutable; assertions need stable target |
| Updating `source_identity.raw_identifier` | Must insert new row instead |
| Cascading assertion updates after identity merge | History must be preserved |

# 07 — Forensics & Medical Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: Phase 2 architecture defined; MVP stubs in Phase 1

---

## 1. Current Status

**MVP Phase 1**: Stub tables only (`forensic_report`, `medical_report`)
**Phase 2**: Full forensic and medical chain-of-custody model

---

## 2. Forensic Evidence Architecture (Phase 2)

```
evidence_artifact (physical file/image)
        ↓
evidence_instance (case-scoped)
        ↓
forensic_sample (biological / trace / digital sample)
        ↓
sample_collection (when, where, by whom)
        ↓
sample_container (chain-of-custody physical container)
        ↓
sample_transfer (each hand-off event)
        ↓
chain_of_custody_event (audit of every transfer)
        ↓
lab_examination (lab received sample)
        ↓
test_method + instrument + lab_technician
        ↓
lab_result (raw result data)
        ↓
reference_profile (known reference — e.g., person's DNA)
        ↓
comparison (result vs reference)
        ↓
forensic_finding (conclusion: MATCH / EXCLUSION / INCONCLUSIVE)
        ↓
assertion(DNA_MATCHES or DNA_EXCLUDED)
        ↓
hypothesis_support
```

## 3. Medical Evidence Architecture (Phase 2)

```
investigative_case
        ↓
medical_examination (who was examined, by whom, when)
        ↓
autopsy / postmortem (if applicable)
        ↓
medical_finding (documented observations)
        ↓
injury, cause_of_death, manner_of_death
        ↓
toxicology_result
        ↓
medical_evidence (links to evidence_artifact — photos, reports)
        ↓
assertion(CAUSE_OF_DEATH_IS, HAS_INJURY, TIME_OF_DEATH_IS)
```

## 4. Key Forensic Design Rules

- Chain of custody must be continuous — any gap is a `data_quality_issue(CUSTODY_GAP)`
- Forensic findings may be exculpatory — `DNA_EXCLUDED` must be represented (see `05_EPISTEMIC_MODEL.md`)
- Medical records contain sensitive personal data — subject to `legal_restriction` and elevated `clearance_level` requirements
- Autopsy findings are assertions, not person attributes — `cause_of_death` is an `assertion(CAUSE_OF_DEATH_IS)`, not a field on `person`
- Lab instruments must be tracked for instrument calibration validity

## 5. Phase 2 Table List (Architectured, Not Yet Implemented)

```
civix.forensic_sample
civix.sample_collection
civix.sample_container
civix.sample_split
civix.sample_transfer
civix.chain_of_custody_event
civix.lab_examination
civix.test_method
civix.instrument
civix.lab_technician
civix.lab_result
civix.reference_profile
civix.comparison
civix.forensic_finding
civix.medical_examination
civix.medical_finding
civix.injury
civix.autopsy
civix.cause_of_death_record
civix.toxicology_result
civix.medical_evidence_link
```

## 6. MVP Stubs (Phase 1)

```sql
civix.forensic_report:
  report_id UUID PK
  instance_id UUID FK → evidence_instance
  report_type TEXT NOT NULL
  lab_name TEXT NULL
  examiner_name TEXT NULL
  findings_summary TEXT NULL

civix.medical_report:
  report_id UUID PK
  instance_id UUID FK → evidence_instance
  examination_type TEXT NOT NULL
  findings_summary TEXT NULL
  practitioner_name TEXT NULL
  examination_date DATE NULL
```

These stubs allow Phase 1 ingestion while Phase 2 tables are implemented.
The `instance_id` FK ensures they are provenance-traceable.

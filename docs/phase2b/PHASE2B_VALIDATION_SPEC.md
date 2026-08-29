# CIVIX — PHASE 2B VALIDATION SPEC
## verify_phase2b.py Test Specifications

**Version**: 1.0 | **Date**: 2026-08-29
**Authority**: SYNTHETIC_DATA_ENGINE_DESIGN.md Section N

---

## Test Groups

### A. Row Count Tests
| Test | Expected Value | Query |
|---|---|---|
| A01 | persons = 55 | `SELECT count(*) FROM civix.person` |
| A02 | networks = 3 | `SELECT count(*) FROM civix.network` |
| A03 | organizations = 16 | `SELECT count(*) FROM civix.organization` |
| A04 | phone_numbers ≥ 42 | `SELECT count(*) FROM civix.phone_number` |
| A05 | vehicles = 13 | `SELECT count(*) FROM civix.vehicle` |
| A06 | properties ≥ 8 | `SELECT count(*) FROM civix.property` |
| A07 | devices ≤ 11 | `SELECT count(*) FROM civix.device` (UNKNOWN-IMEI → SI) |
| A08 | CALL events ≥ 385 | `SELECT count(*) FROM civix.event WHERE event_type='CALL'` |
| A09 | TRANSACTION events = 50 | `SELECT count(*) FROM civix.event WHERE event_type='TRANSACTION'` |
| A10 | PROPERTY_MUTATION events = 3 | `SELECT count(*) FROM civix.event WHERE event_type='PROPERTY_MUTATION'` |
| A11 | source_records ≥ 450 | `SELECT count(*) FROM civix.source_record` |
| A12 | assertions ≥ 440 | `SELECT count(*) FROM civix.assertion` |
| A13 | hypotheses ≥ 4 | `SELECT count(*) FROM civix.hypothesis` |
| A14 | investigative_cases = 4 | `SELECT count(*) FROM civix.investigative_case` |
| A15 | provenance ≥ 440 | `SELECT count(*) FROM civix.provenance` |

---

### B. Foreign-Key Integrity Tests
| Test | Checks |
|---|---|
| B01 | All entity subtypes have a matching entity supertype row |
| B02 | All event_participant.entity_id exist in entity |
| B03 | All assertion.subject_entity_id exist in entity |
| B04 | All hypothesis.case_id exist in investigative_case |
| B05 | All hypothesis_support.(hypothesis_id, assertion_id) exist |
| B06 | All evidence_instance.(artifact_id, case_id) exist |
| B07 | All case_entity_role.(case_id, entity_id) exist |
| B08 | All identity_candidate.(source_identity_id, proposed_person_id) exist |

---

### C. Orphan Detection Tests
| Test | Checks |
|---|---|
| C01 | No person with no source_identity and no assertion |
| C02 | No evidence_artifact with no evidence_instance |
| C03 | No observation with missing evidence_instance |
| C04 | No extraction with missing analysis_run |
| C05 | No assertion with no provenance record |
| C06 | No event with zero event_participants |

---

### D. Temporal Integrity Tests
| Test | Checks |
|---|---|
| D01 | No sim_number_assignment overlaps for same phone_number (GIST exclusion working) |
| D02 | No sim_in_device overlaps for same sim (GIST exclusion working) |
| D03 | All event.occurred_at has lower <= upper |
| D04 | All account_holder.valid_time lower <= upper |
| D05 | All source_identity.tx_end > tx_start (if tx_end IS NOT NULL) |
| D06 | No CDR event has occurred_at outside 2026-06-01 to 2026-08-31 |

---

### E. Provenance Completeness Tests
| Test | Checks |
|---|---|
| E01 | Every assertion has ≥1 provenance record |
| E02 | Every extraction has a provenance record tracing to evidence_instance |
| E03 | Every observation has a provenance record tracing to source_record |
| E04 | No dangling provenance records (source_id not referencing anything) |

---

### F. Evidence Chain Integrity Tests
| Test | Checks |
|---|---|
| F01 | Every evidence_artifact has a valid sha256_hash (non-null, BYTEA) |
| F02 | No duplicate (sha256_hash, hash_algorithm) pairs |
| F03 | Every evidence_instance links to a valid case |
| F04 | Evidence pipeline complete: source_record → evidence_artifact → evidence_instance → observation |
| F05 | Derived artifact chain: at least one parent_artifact_id exists in evidence_artifact |

---

### G. Identity Resolution Integrity Tests
| Test | Checks |
|---|---|
| G01 | No Person was auto-created without an identity_resolution record |
| G02 | All ACCEPTED identity_resolution records have resolved_person_id NOT NULL |
| G03 | No source_identity with identifier_type=IMEI AND raw_identifier='UNKNOWN-IMEI' has a device row |
| G04 | Every person has ≥1 source_identity pointing to them via identity_resolution |
| G05 | Ambiguous identity: ≥2 identity_candidate rows with different proposed_person_id for at least 1 source_identity |

---

### H. Telecom Relationship Tests
| Test | Checks |
|---|---|
| H01 | Every phone_number entity appears in ≥1 event_participant(CALLER or CALLEE) |
| H02 | CDR SIM sharing anomaly exists: caller_msisdn=Ravi's number + imei=Bhupendra's device |
| H03 | At least 1 sim_in_device record exists |
| H04 | At least 1 sim_number_assignment record exists |

---

### I. Financial Relationship Tests
| Test | Checks |
|---|---|
| I01 | Joint account PNB-****8877 has ≥2 account_holders (P-02 Amit, P-09 Harish) |
| I02 | Every financial_account appears in ≥1 account_holder record |
| I03 | "Network Beta)" is a source_identity NOT a financial_account |
| I04 | SIG-05: Dinesh's account has ≥3 credit transactions of ~equal amounts (≥₹100,000 each) |
| I05 | SIG-06: Deepak's account has a single ₹75,000 credit transaction |

---

### J. Property Relationship Tests
| Test | Checks |
|---|---|
| J01 | PROP-01 entity exists (Khasra 45) |
| J02 | PROP-08 entity exists (Khasra 45 adjacent) |
| J03 | PROP-02 and PROP-03 entities exist |
| J04 | All 8 property entities have a corresponding entity supertype row |
| J05 | P-12 (Sunita) is RECEIVED_PROPERTY for PROP-01 (assertion exists) |

---

### K. N-Ary Events (H4) Tests
| Test | Checks |
|---|---|
| K01 | The PROPERTY_MUTATION event has EXACTLY 2 TARGET_PROPERTY participants (PROP-01 and PROP-08) |
| K02 | The same event has PREVIOUS_OWNER = P-14 (Kamla Bai) |
| K03 | The same event has NEW_OWNER = P-12 (Sunita Agarwal) |
| K04 | Both PROP-01 and PROP-08 reference Khasra 45 in their property_ref or description |
| K05 | No PROP-04 appears as TARGET_PROPERTY in this event (regression guard) |

---

### L. Investigative Signal Tests

#### L-SIG-03 (Suresh movement anomaly)
```sql
-- Find Suresh's events that include geographically separated cell towers
WITH suresh_events AS (
  SELECT ep.event_id FROM civix.event_participant ep
  JOIN civix.source_identity si ON ep.entity_id = si.entity_id
  JOIN civix.identity_resolution ir ON ir.source_identity_id = si.entity_id
  JOIN civix.person p ON ir.resolved_person_id = p.entity_id
  WHERE p.display_name ILIKE '%Suresh%'
    AND ep.participant_role = 'CALLER'
)
SELECT count(*) FROM suresh_events;
-- Must be > 0; geographic validation done by spatial distance check on cell tower geometry
```

#### L-SIG-05 (Dinesh corruption deposits)
```sql
-- Dinesh's account receives 3 large equal deposits
SELECT count(*) FROM civix.event_participant ep
JOIN civix.observation o ON o.instance_id IN (
  SELECT instance_id FROM civix.evidence_instance WHERE case_id IN (
    SELECT case_id FROM civix.investigative_case WHERE case_number LIKE 'CIV-ALPHA%'
  )
)
-- Expected: ≥3 matching observations
```

#### L-SIG-08 (Periodic communications)
```sql
-- Bhupendra and Gopal monthly calls
SELECT count(DISTINCT date_trunc('month', lower(e.occurred_at))) AS distinct_months
FROM civix.event e
JOIN civix.event_participant ep1 ON e.event_id = ep1.event_id
JOIN civix.event_participant ep2 ON e.event_id = ep2.event_id
WHERE e.event_type = 'CALL'
  AND ep1.participant_role = 'CALLER'
  AND ep2.participant_role = 'CALLEE'
  -- Bhupendra and Gopal source_identities
;
-- Expected: 3 distinct months (June, July, August)
```

#### L-FL-06 (Rekha Verma false lead)
```sql
-- Rekha Verma investigative lead classified FALSE_POSITIVE
SELECT count(*) FROM civix.investigative_lead il
WHERE il.lead_text ILIKE '%Rekha%'
  AND il.status = 'FALSE_POSITIVE';
-- Expected: ≥1
```

---

### M. Case Access Tests
| Test | Checks |
|---|---|
| M01 | CIV-ALPHA-001, CIV-BETA-001, CIV-GAMMA-001, CIV-CROSS-001 all exist |
| M02 | Each case has ≥2 case_access records |
| M03 | No user has default READ to all 4 cases (cross-case isolation exists) |
| M04 | Revocation test: ≥1 case_access record with is_revoked=TRUE |

---

### N. RLS Behavior Tests
| Test | Checks |
|---|---|
| N01 | RLS enabled on investigative_case |
| N02 | RLS enabled on evidence_instance |
| N03 | RLS enabled on assertion |
| N04 | RLS enabled on hypothesis |
| N05 | policy_assertion_select policy exists |
| N06 | policy_case_access policy exists |

---

### O. Tombstone Tests
| Test | Checks |
|---|---|
| O01 | At least 1 entity has visibility_status = TOMBSTONED |
| O02 | Tombstoned entity has a corresponding TOMBSTONE_NODE outbox record |
| O03 | Tombstoned entity's related records are accessible to ADMIN but filtered for standard queries |

---

### P. Bitemporal Reconstruction Tests
| Test | Checks |
|---|---|
| P01 | AS-OF query: hypothesis_support has bitemporal rows (1 closed + 1 active) after an update |
| P02 | AS-OF reconstruction returns exactly 1 active row for a bitemporal entity at any point in time |
| P03 | tx_end is NULL for all currently active rows |

---

### Q. Deterministic Regeneration Tests
| Test | Checks |
|---|---|
| Q01 | Run 1 generates same generation_run_id UUID as Run 2 (same seed) |
| Q02 | All person entity_id UUIDs match between Run 1 and Run 2 |
| Q03 | Total row counts identical between Run 1 and Run 2 |
| Q04 | SHA-256 of all assertion PKs sorted lexicographically is identical between Run 1 and Run 2 |

---

### R. Negative Tests (Adversarial)
| Test | Checks |
|---|---|
| R01 | INSERT assertion with free-text predicate → FK violation (predicate not in enum) |
| R02 | INSERT audit_event then UPDATE it → trigger rejection |
| R03 | INSERT entity then DELETE it → trigger rejection (tombstone required) |
| R04 | INSERT hypothesis with status=CONFIRMED and confirmed_by=NULL → CHECK violation |
| R05 | INSERT two sim_number_assignment rows for same phone_number with overlapping valid_time → GIST exclusion |
| R06 | INSERT identity_resolution with status=ACCEPTED and resolved_person_id=NULL → CHECK violation |
| R07 | INSERT duplicate evidence_artifact with same (sha256_hash, hash_algorithm) → UNIQUE violation |

---

### S. Scale Smoke Tests (Mode B only)
| Test | Checks |
|---|---|
| S01 | 500 persons inserted without FK violations |
| S02 | 3850 CDR events inserted with correct event_participant structure |
| S03 | No performance timeout: all 500-person inserts complete in <60 seconds |
| S04 | Deterministic: re-running scale mode with same seed produces same row counts |

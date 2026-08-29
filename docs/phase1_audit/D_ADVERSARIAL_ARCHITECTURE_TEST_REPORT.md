# D — ADVERSARIAL ARCHITECTURE TEST REPORT
## CIVIX Phase 1 — 30 New Adversarial Scenarios

**Date**: 2026-08-29 | **Status**: FINAL

> [!IMPORTANT]
> These are NEW scenarios, distinct from the 30 adversarial tests in `CIVIX_SCHEMA_HARDENING_REPORT.md`.
> Each scenario tests a specific architectural edge case.
> PASS = architecture handles this correctly
> FAIL = architecture fails or is undefined
> PARTIAL = architecture partially handles this; gap identified

---

## Identity & Resolution Adversarial Tests

### ADV-01: Father and Son Share Exact Same Name and Village
**Scenario**: Ramesh Kumar (P-19) has a son also named Ramesh Kumar living at the same address. CDR data and a bank account appear in the name "Ramesh Kumar." An AI extractor creates two SourceIdentity rows (one from CDR, one from bank) and proposes them as the same person.

**Expected**: Two distinct source_identity rows. `identity_candidate` creates a proposal linking both to the same Person. But NO merge happens without human decision. The younger Ramesh Kumar becomes a new Person entity only if evidence establishes he exists independently.

**Current architecture behavior**:
- PASS: `identity_candidate` links source_identity → proposed_person with `is_active=TRUE`
- PASS: No auto-merge (INV-07 prohibits it)
- PARTIAL: No mechanism to record "this source_identity has been confirmed as DIFFERENT from Person X." `identity_resolution(status=REJECTED)` exists — but does that mean "this source_identity is not Person X" or "we haven't decided yet"?
- **GAP**: `REJECTED` in `identity_resolution_status_enum` does not distinguish "confirmed different person" from "inconclusive — no decision." REFUTED would be clearer.

**Status**: **PARTIAL** — REJECTED is semantically ambiguous.

---

### ADV-02: Three Suspects Have Same Phone Number in Sequence (Handset Resale)
**Scenario**: Phone number 9876543210 was used by:
- P-01 (Vikram Singh): June 1 – June 15
- Unknown person: June 16 – June 28 (number reassigned)
- P-02 (Amit Verma): July 1 – August 31

CDR records show calls from 9876543210 without knowing which person was using it at which time.

**Expected**: `sim_number_assignment` correctly tracks which SIM had this number at each time. `event_participant(CALLER, source_identity=phone)` makes no claim about person identity during uncertain periods.

**Current architecture behavior**:
- PASS: `sim_number_assignment` with GIST exclusion constraint handles temporal exclusivity of SIM-MSISDN assignment
- PASS: CDR events link to `source_identity(PHONE_MSISDN)`, not directly to Person
- PASS: Temporal uncertainty is preserved — no auto-attribution
- **GAP (new)**: There is no `person_phone_use` table. A person's USE of a phone number is represented only via assertions (HAD_NUMBER predicate). But temporal tracking of person-number usage is not directly queryable via schema — must be inferred from assertions with valid_from/valid_to. This is correct but must be documented.

**Status**: **PASS**

---

### ADV-03: SIM Card Appears in Two Devices on Same Day (Conflicting CDRs)
**Scenario**: ICCID-1234 is recorded in IMEI-8811 at 14:30 and in IMEI-8833 at 14:45 on the same day. This is physically impossible for one SIM.

**Expected**: `sim_in_device` GIST exclusion constraint rejects the second insert. A `data_quality_issue(TEMPORAL_IMPOSSIBILITY)` is created.

**Current architecture behavior**:
- PASS: `EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)` will reject the conflicting insert
- PASS: `data_quality_issue` table captures the conflict
- **GAP**: What happens to the second CDR record that references the conflicting SIM state? The source_record is still ingested. The observation is still created. But the `sim_in_device` constraint fails. There is no defined pipeline for "what happens when a physical constraint violation is discovered during CDR ingestion." The ingestion pipeline must handle the constraint exception gracefully.

**Status**: **PARTIAL** — constraint enforced but exception handling pipeline undefined.

---

### ADV-04: Person's Identity Merge, Then Disagreeing Expert
**Scenario**: SourceIdentity A (from CDR) and SourceIdentity B (from FIR) are merged into Person P-07 by Investigator Ravi. Two weeks later, forensic evidence proves they are different people. Investigator Priya creates a split event.

After the split:
- SourceIdentity A remains with Person P-07
- SourceIdentity B is reassigned to Person P-99 (new entity)

**Question**: Do assertions made against SourceIdentity B remain attributed to SourceIdentity B (correct) or do they need to be re-targeted?

**Expected**: All assertions targeted at `source_identity_b.entity_id` remain unchanged. The `identity_split_event` records the correction. Downstream hypotheses that referenced P-07 may now be wrong (they thought P-07 committed act X, but act X was done by the now-separate P-99).

**Current architecture behavior**:
- PASS: `identity_split_event` records the correction with `original_resolution_id` and `new_person_b_id`
- PASS: Assertions against SourceIdentity B are stable because assertions target entity_id (the source_identity's entity_id), not the canonical Person
- PASS: The identity_resolution row for SourceIdentity B is superseded
- **GAP**: Hypotheses that referenced Person P-07 as SUBJECT are not automatically updated. A hypothesis might read "P-07 was present at the crime scene." If P-07's identity included SourceIdentity B (now re-attributed to P-99), the hypothesis's evidentiary basis changes but the hypothesis text still reads "P-07." The architecture has no automatic re-evaluation trigger.
- **Mitigation**: `data_quality_issue` is created on split, flagging affected hypotheses for re-evaluation.

**Status**: **PASS** (with known risk — human re-evaluation required after split)

---

### ADV-05: Unresolved Person Appears Only in CCTV
**Scenario**: CCTV footage shows an unidentified person (UNKNOWN-FACE-001) at a crime scene. No name, no phone, no vehicle. Only a face.

**Expected**: A `source_identity(identifier_type=FACE_EMBEDDING_REF, raw_identifier='FACE-EMBEDDING-20260813-14430')` is created. No Person is created yet. An `identity_candidate` may propose links to known persons, but no automatic merge.

**Current architecture behavior**:
- PASS: `source_identity_type_enum` includes `FACE_EMBEDDING_REF`
- PASS: Person is not created (INV-07)
- PASS: `identity_candidate` can propose links
- **GAP (new)**: There is no `face_embedding` or `biometric_artifact` table. The actual embedding vector (a float array) is referenced only by ID in `raw_identifier`. Where is the embedding stored? The architecture has no vector store or biometric artifact repository.
- **GAP (new)**: For face recognition matching, you need the embedding vectors. Storing them as a string reference ("FACE-EMBEDDING-20260813-14430") with no table for the actual data is incomplete.

**Status**: **PARTIAL** — identifier pattern defined, but biometric artifact storage undefined.

---

### ADV-06: Same Evidence File Appears in Three Different Cases
**Scenario**: A CDR export file (SHA256: ABC123...) is relevant to Case A (drug trafficking), Case B (money laundering), and Case C (murder). The same file should not be stored three times.

**Expected**: One `evidence_artifact` row. Three `evidence_instance` rows — one per case, each with its own `legal_status`, `acquired_by`, and `acquisition_context`.

**Current architecture behavior**:
- PASS: `UNIQUE(sha256_hash, hash_algorithm)` ensures one artifact
- PASS: `evidence_instance.case_id NOT NULL` links each instance to its case
- PASS: Three instances for three cases is the correct design

**Status**: **PASS**

---

### ADV-07: Person A Has Valid Alibi That Contradicts Hypothesis H1
**Scenario**: P-03 (Suresh Khan) is the primary suspect in H1. A hospital timestamp photo places P-03 at Hospital X at the exact time of the alleged crime. P-03's lawyer submits this as exculpatory evidence.

**Expected**:
1. Artifact → EvidenceInstance (case)
2. Observation: "P-03 photographed at Hospital X at 14:30:22 Aug 13"
3. Assertion: `P-03 ALIBI_CONFIRMED_AT Hospital-X, valid_from=14:30, valid_to=15:30, epistemic_status=CONFIRMED`
4. `hypothesis_support(assertion_id=alibi_assertion, hypothesis_id=H1, stance=CONTRADICT, weight=0.9)`

**Current architecture behavior**:
- PASS: `ALIBI_CONFIRMED_AT` exists in predicate_enum
- PASS: `hypothesis_support.stance=CONTRADICT` supported
- PASS: Assertion is separate from hypothesis — one assertion can contradict one hypothesis while being neutral to another
- PASS: Exculpatory evidence uses identical pipeline — no special case

**Status**: **PASS**

---

### ADV-08: Duplicate CCTV Recordings from Two Camera Systems
**Scenario**: The same 2-hour window is captured by both CCTV-Node-7 (HIGH-RES) and CCTV-Node-3 (LOW-RES). They have different SHA256 hashes (different files) but cover the same real-world event.

**Expected**: Two separate `evidence_artifact` rows (different hashes). Both can be associated to the same event via `event_participant(OBSERVER, CCTV-Node-7-location)`. They are not deduplicated because they are genuinely different files.

**Current architecture behavior**:
- PASS: `UNIQUE(sha256_hash, hash_algorithm)` — different files with different hashes → two artifact rows
- PASS: Both can be linked to the same event via event_participant
- **GAP**: There is no "coverage overlap" detection. If investigator wants to know "do we have redundant footage of event E?" there is no query path to answer that. Would require comparing observation timestamps.

**Status**: **PASS** (coverage overlap query is future feature, not architecture blocker)

---

### ADV-09: Financial Transaction With Unknown Counterparty
**Scenario**: `TX-000025`: `BOB-****3345 → Network Beta), ₹18,569`. The receiver "Network Beta)" is not a known financial account — it's a garbled string (probably an organization or error).

**Expected**: "Network Beta)" becomes a `source_identity(identifier_type=OTHER, raw_identifier='Network Beta)')`. It is NOT a `financial_account` entity. An assertion `BOB-****3345 TRANSFERRED_TO source_identity:'Network Beta)'` is created.

**Current architecture behavior**:
- PASS: `03_DATABASE_SCHEMA_BIBLE.md` explicitly documents this mapping (GAP-19 closed)
- PASS: `source_identity` accepts `OTHER` type
- **GAP**: The assertion's `object_entity_id` would point to the source_identity entity. But the `predicate_enum` has `TRANSFERRED_TO` which semantically implies a financial account. Is it valid to TRANSFERRED_TO a source_identity? The predicate vocabulary does not constrain valid object entity types for each predicate.
- **GAP (new)**: There is no predicate constraint table mapping `predicate → allowed_object_types`. The current architecture allows `P-01 CALLED network-beta)` — semantically nonsensical but not database-rejected.

**Status**: **PARTIAL** — semantic predicate-object type constraints not enforced.

---

### ADV-10: Multi-Hop Property Fraud (H4 Extended)
**Scenario**: Kamla Bai (P-14) sells Khasra-45 to Sunita Agarwal (P-12). Then Sunita transfers it again to Bharat (P-15). The full chain is: Kamla → Sunita → Bharat. This requires two `PROPERTY_MUTATION` events.

**Expected**: 
- Event E7: `(P-14 PREVIOUS_OWNER, P-12 NEW_OWNER, Khasra-45 TARGET_PROPERTY)`
- Event E8: `(P-12 PREVIOUS_OWNER, P-15 NEW_OWNER, Khasra-45 TARGET_PROPERTY)`

Two separate events. The chain is queryable.

**Current architecture behavior**:
- PASS: N-ary event design supports multiple PROPERTY_MUTATION events for the same property
- PASS: `event_participant(TARGET_PROPERTY)` links each event to the affected property
- PASS: From the actual data, property_transfers.csv has 3 rows: PROP-01 (Khasra 45), PROP-02 (Khasra 88), PROP-03 (Khasra 92). All going to P-12. This represents three SEPARATE property mutation events, not a chain. H4 is correctly one event per CSV row → one event per mutation.

**Status**: **PASS**

---

### Temporal / Bitemporal Tests

### ADV-11: Late-Arriving Evidence Changes Timeline
**Scenario**: On Aug 29, CIVIX receives a bank statement showing P-02 transferred ₹200,000 to P-09 on June 5 (tx_time = now, valid_time = June 5). This retroactively strengthens a hypothesis that was assessed as PROBABLE on June 30.

**Expected**: The assertion is created with `valid_from = June 5` (real-world time) and `tx_start = Aug 29` (when CIVIX learned of it). The hypothesis_support created on June 30 was based on information available at that time. The new late-arriving evidence creates a new hypothesis_support row. Historical re-evaluation shows the evidence was always true, just unknown.

**Current architecture behavior**:
- PASS: `assertion.valid_from/valid_to` captures real-world validity
- PASS: `assertion.tx_start` captures when CIVIX recorded it
- PASS: `hypothesis_support.tx_start` exists (after BLK-06 fix)
- PASS: AS-OF queries can show hypothesis state at June 30 vs now

**Status**: **PASS** (requires BLK-06 fix to hypothesis_support for full bitemporal support)

---

### ADV-12: Historical Feature Extraction Uses Future Information
**Scenario**: ML model is trained in September. To avoid leakage, features for August 13 (crime day) must not include any evidence that CIVIX learned AFTER August 13. A CDR record received August 25 but describing a June 15 call must be excluded from features for the "as of August 13" snapshot.

**Expected**: Filter on `assertion.tx_start <= '2026-08-13'` to get only assertions that were known by August 13.

**Current architecture behavior**:
- PASS: Bitemporal `tx_start/tx_end` columns on assertion allow this query
- PASS: `generation_run_id` filters synthetic vs production data
- PASS: `analysis_run.input_snapshot_tx_time` captures the temporal cutoff used in a training run

**Status**: **PASS**

---

### ADV-13: Evidence Time Window Contains Significant Uncertainty
**Scenario**: A physical meeting is believed to have occurred "sometime in July 2026" — no exact date. A witness says "it was a Saturday, probably mid-July."

**Expected**: `event.occurred_at = TSTZRANGE('[2026-07-04, 2026-07-25]')` (bounding the possible Saturdays in mid-July). The range represents real uncertainty, not a specific time.

**Current architecture behavior**:
- PASS: `event.occurred_at TSTZRANGE NOT NULL` explicitly supports time ranges
- **GAP (new)**: There is no `temporal_confidence DECIMAL` on event to indicate how tight/wide the range is. A range of 3 weeks vs a range of 2 seconds both look the same in the schema.
- PASS (acceptable): The range width itself conveys confidence. Explicit confidence score may be optional.

**Status**: **PASS** (temporal confidence via range width is sufficient)

---

### Provenance / Chain-of-Custody Tests

### ADV-14: Compromised Source — 5,000 CDRs Poisoned
**Scenario**: A seized device (IMEI-8811) is later found to have been tampered with. The tampering happened AFTER seizure but before digital examination. This compromises 5,000 CDR records extracted from the device.

**Expected**: 
1. `data_quality_issue(CUSTODY_GAP, severity=CRITICAL)` created for IMEI-8811
2. Provenance traversal finds all `evidence_instance → observation → extraction → assertion` rows derived from this device
3. Provenance risk is recomputed dynamically — affected assertions show elevated risk
4. No cascading UPDATE to historical assertions (INV-11: provenance risk is computed, never stored)
5. Investigator is alerted to re-evaluate 20 hypotheses that used these assertions

**Current architecture behavior**:
- PASS: `data_quality_issue` table captures the quality event
- PASS: Provenance risk is computed dynamically (INV-11 preserved)
- PASS: No cascading writes
- PARTIAL: The mechanism for "which hypotheses used assertions from IMEI-8811" requires a recursive CTE over the provenance table. Performance depends on indexes (BLK-16 addresses this).
- **GAP**: There is no defined trigger or notification mechanism that automatically alerts investigators when provenance risk escalates on their active hypotheses. This must be a background job.

**Status**: **PARTIAL** — correct design, but notification/alerting mechanism undefined.

---

### ADV-15: Chain of Custody Gap — Sample Not Logged During Transfer
**Scenario**: A physical evidence bag is transferred from field to lab. The field officer signs out at 10:00. The lab signs in at 14:30. No record exists for the 4.5-hour gap. This is a CUSTODY_GAP.

**Expected**: When chain-of-custody events are entered, the system detects the temporal gap and creates `data_quality_issue(CUSTODY_GAP)`.

**Current architecture behavior**:
- **FAIL (MVP)**: The MVP schema has `forensic_report` as a stub with only a `findings_summary TEXT` field. There is no `chain_of_custody_event` table in the MVP phase. This scenario cannot be represented in MVP.
- PASS (Phase 2): `07_FORENSICS_AND_MEDICAL_BIBLE.md` documents `chain_of_custody_event` for Phase 2.
- The gap-detection logic (comparing transfer-out and transfer-in timestamps) must be an application-layer check.

**Status**: **FAIL** (Phase 1 MVP only) — deferred to Phase 2 per documented decision.

---

### ADV-16: Same Physical Evidence Item Has Multiple Lab Examinations With Conflicting Results
**Scenario**: A knife (forensic sample) is examined by Lab A: "Blood type O." Same knife examined by Lab B (requested by defense): "Blood type AB." Conflicting findings.

**Expected**: Two separate `lab_examination` records, each with their own `lab_result`. Both findings are represented. A `data_quality_issue(CONTRADICTORY_DATA)` is created. Neither result is deleted. The investigation task includes resolving the conflict.

**Current architecture behavior**:
- **FAIL (MVP)**: No `lab_examination` or `lab_result` table in MVP phase. `forensic_report` stub cannot represent multiple examinations with distinct findings.
- PASS (Phase 2): Architectured in `07_FORENSICS_AND_MEDICAL_BIBLE.md`.

**Status**: **FAIL** (Phase 1 MVP only)

---

### Security / Access Tests

### ADV-17: Investigator Transfers Between Cases Mid-Investigation
**Scenario**: Officer Vijay Kumar (P-28) is transferred from Case A to Case B on Aug 15. He should lose WRITE access to Case A but retain READ for continuity. After Aug 20, he should lose READ too.

**Expected**: Case A's `case_access` record for Vijay:
1. Initially: `permission_level=WRITE, is_revoked=FALSE`
2. Aug 15: Revoke WRITE, create new `case_access(READ, valid_until=Aug 20)`
3. Aug 20: valid_until expires — access lapses

**Current architecture behavior**:
- PARTIAL: `case_access` has `valid_until TIMESTAMPTZ NULL` — time-limited access works
- PARTIAL: Revoking WRITE and creating new READ requires the partial unique index fix (BLK-08)
- PASS (after BLK-08 fix): With partial unique `WHERE is_revoked = FALSE`, this flow works
- **GAP**: `case_access` RLS policy only checks `is_revoked = FALSE AND valid_until > now()`. But the policy shown in `10_SECURITY_RBAC_AUDIT_BIBLE.md` doesn't check `valid_until`. The example RLS policy is incomplete.

**Status**: **PARTIAL** — `valid_until` not enforced in the example RLS policy.

---

### ADV-18: Sealed Evidence — Investigator Sees Lead But Not Source
**Scenario**: Evidence artifact E1 is court-sealed. An investigative lead was generated based on E1. Investigator has READ access to the case but should not see E1's content.

**Expected**: 
- `legal_restriction(SEALED)` created on E1
- RLS on `evidence_instance` filters E1 from the investigator's view
- The `investigative_lead` text is still visible (leads don't directly reference artifacts)
- If investigator clicks "show evidence for this lead", E1 is not returned

**Current architecture behavior**:
- PASS: RLS on `evidence_instance` restricts access
- PASS: `legal_status = 'SEALED'` on the evidence_instance is set
- **GAP**: The `investigative_lead` table has no FK to `evidence_artifact` or `evidence_instance`. The provenance link from lead → assertion → extraction → evidence_instance is via the provenance table (app-layer FKs). So the UI/API must traverse provenance to find which evidence supports a lead — and filter sealed evidence at that traversal layer. This is complex application logic, not DB constraint.
- **FINDING**: No evidence-to-lead RLS. The lead text itself may contain PII from sealed evidence.

**Status**: **PARTIAL** — see BLK-10 for related issue.

---

### ADV-19: Two Investigations Share a Suspect — Need Separate Hypothesis Tracks
**Scenario**: P-02 (Amit Verma) is a suspect in Case A (financial fraud) AND Case B (property fraud). Each case has its own hypothesis about Amit. Evidence from Case A cannot be shared to Case B without explicit authorization.

**Expected**: Two cases, two separate `hypothesis` rows (each with their own case_id). Evidence instance E1 belongs to Case A. To share it, `case_link` must be created. Assertions derived from Case A evidence would only appear in Case B's hypothesis_support after authorization.

**Current architecture behavior**:
- PASS: `hypothesis.case_id` isolates hypotheses by case
- PASS: `evidence_instance.case_id` isolates evidence by case
- PASS: `case_link` with `share_scope` controls what can be shared
- **GAP**: Can an assertion from Case A be used in Case B's hypothesis without creating a `case_link`? Technically yes — the assertion table has no `case_id`. Assertions are case-agnostic. This means any user with write access to any case can create a `hypothesis_support` row linking any assertion to any hypothesis, regardless of whether they have access to the evidence that produced the assertion.
- **FINDING**: Assertions need case-level access control, or `hypothesis_support` needs to check that the user has access to the evidence chain.

**Status**: **FAIL** — assertion cross-case access control gap.

---

### ADV-20: EXPUNGED Entity — Checking All Downstream Effects
**Scenario**: P-99 (minor — later found to be under 18 at time of recording) is expunged by court order. P-99 appeared in:
- 12 event_participant rows
- 3 assertions as subject
- 2 assertions as object_entity_id
- 1 investigative_lead with lead_text containing "P-99 was seen..."
- 2 hypothesis_support rows
- 1 FIR complainant_entity_id

**Expected**: PostgreSQL row retained but invisible via RLS. Neo4j node DETACH DELETEd. lead_text sanitized. FIR complainant_entity_id nullified or marked.

**Current architecture behavior**:
- PASS: `legal_restriction(EXPUNGED)` created
- PASS: Outbox tombstone issued, Neo4j DETACH DELETE
- PARTIAL: `investigative_lead.lead_text` contains free text with PII — see BLK-10
- PARTIAL: `fir.complainant_entity_id FK→entity` — if P-99 is expunged, this FK still points to P-99's entity. RLS on the entity table would hide P-99, but the FIR record would still exist with a FK to a now-hidden entity. Queries on FIR would return a NULL complainant even though the record exists. This is fragile.
- PARTIAL: `event_participant` rows still exist (they reference the hidden entity_id). Graph queries filtering for P-99 would fail silently if entity is hidden.
- **GAP**: There is no systematic "expunge impact analysis" query defined. A TOMBSTONE_ISSUED audit event is created, but the investigator has no tool to enumerate all records that referenced P-99.

**Status**: **PARTIAL** — expungement flow exists but has multiple edge cases.

---

### AI/ML Tests

### ADV-21: AI Extracts an Entity That Does Not Exist
**Scenario**: An AI NER model extracts "Prime Minister Modi" from a surveillance narrative. This is not a person of investigative interest. The AI creates a source_identity and proposes an identity_candidate linking to an existing Person entity "Narendra Modi" in the database.

**Expected**: Source_identity is created (legitimate). Identity_candidate is created (legitimate — AI proposes). Human review required before any merge (INV-07). The candidate is rejected by the investigator.

**Current architecture behavior**:
- PASS: source_identity created
- PASS: identity_candidate created with `ai_confidence` score
- PASS: Human review required — no auto-merge
- PASS: `identity_resolution(status=REJECTED)` records the rejection
- **GAP (new)**: After rejection, can the AI propose the same (source_identity, person) pair again? `UNIQUE(source_identity_id, proposed_person_id)` on identity_candidate would prevent a new proposal for the same pair unless `is_active` is used. If `is_active=FALSE` after rejection, a new candidate with the same pair would violate the UNIQUE constraint.

**Status**: **PARTIAL** — AI re-proposal of same rejected candidate is unclear.

---

### ADV-22: AI Generates 50 Assertions in One Analysis Run — Then Run Is Found Faulty
**Scenario**: An ML model (analysis_run_id=RUN-42) generates 50 assertion rows and 200 hypothesis_support rows. Later, RUN-42 is found to have used corrupted training data. All 50 assertions are suspect.

**Expected**: RUN-42 is flagged as faulty. All 50 assertions with `source_analysis_run_id=RUN-42` are marked REFUTED or flagged via `data_quality_issue`. The 200 hypothesis_support rows derived from those assertions are re-evaluated.

**Current architecture behavior**:
- PASS: `assertion.source_analysis_run_id FK→analysis_run` links assertions to their source run
- PASS: `extraction.is_superseded BOOL` can mark the extractions from RUN-42
- **GAP**: There is no `analysis_run.status` or `is_voided BOOL` on `analysis_run`. You cannot mark an entire run as faulty. You'd have to update each individual assertion, which is mutable — but assertions have no `is_superseded` or `tx_end` field (unlike extraction). 
- **FINDING**: Assertions have no supersession mechanism. The `tx_end` on assertion handles bitemporal end-of-validity, but the Bible doesn't define what sets `tx_end` and whether a REFUTED assertion's `tx_end` should be set.

**Status**: **FAIL** — no analysis_run invalidation mechanism, assertions have no supersession.

---

### ADV-23: Low-Confidence OCR Creates Partially-Wrong Extraction
**Scenario**: A scanned FIR document is OCRed. OCR confidence is 0.62 for the name field, producing "Amrit Sharma" when the actual name is "Amrit Varma." This incorrect extraction leads to a source_identity being created.

**Expected**: `extraction(ai_confidence=0.62, extracted_value={"name": "Amrit Sharma"}, extraction_type=OCR)`. The low confidence should prevent this from being automatically converted to a high-epistemic-status assertion. A `data_quality_issue(MISSING_REQUIRED_FIELD or CONTRADICTORY_DATA)` may be appropriate.

**Current architecture behavior**:
- PASS: `extraction.ai_confidence DECIMAL(5,4)` captures the 0.62 confidence
- PASS: High confidence threshold before assertion creation is an application-layer rule (not DB constraint)
- **GAP**: There is no DB constraint that prevents creating an `assertion(epistemic_status=CONFIRMED)` from an `extraction(ai_confidence=0.30)`. The application must enforce confidence thresholds. There is no metadata on assertion linking it to its source extraction confidence.

**Status**: **PARTIAL** — confidence captured but not DB-enforced as assertion quality gate.

---

### ADV-24: Graph Community Detection Includes Innocent Peripheral Contacts
**Scenario**: Louvain community detection identifies a community containing P-23 (Rekha Verma — the false positive). Rekha is placed in the same community as Amit Verma (P-02) because she shares an address and a joint bank account. The ML model assigns her a high criminality score.

**Expected**: The graph algorithm should treat Rekha's community membership as a weak signal, not evidence of guilt. The architecture should NOT allow `network_membership ≠ guilt` to be violated (INV-16).

**Current architecture behavior**:
- PASS: INV-16 documented — "Network membership ≠ guilt"
- **FAIL (design gap)**: There is no DB mechanism preventing an ML model from creating an assertion like `Rekha MEMBER_OF criminal-network` based purely on community detection output. The ML pipeline (Phase 10) is not constrained by DB schema.
- **GAP**: If community detection output feeds assertion creation, there is no minimum confidence requirement or human review gate for community-based assertions. The `assertion.epistemic_status` can be set to CONFIRMED by application code even for weak ML signals.
- **Critical**: `assertion.asserted_by` OR `source_analysis_run_id` must be populated (CHECK constraint). But both can be NULL simultaneously? Re-reading line 472: `CHECK (asserted_by IS NOT NULL OR source_analysis_run_id IS NOT NULL)` — correct, one must be populated.

**Status**: **PARTIAL** — INV-16 documented but not DB-enforced for ML-generated assertions.

---

### ADV-25: Two Hypotheses Supported by Same Assertion, Contradictory Stances
**Scenario**: Assertion A1: "P-02 TRANSFERRED_TO P-09, ₹200,000, Aug 13." This:
- SUPPORTS H1: "Amit paid Harish for drug delivery"
- CONTRADICTS H2: "Aug 13 payment was Amit's salary advance (innocent)"

**Expected**: Two `hypothesis_support` rows:
- `(H1, A1, stance=SUPPORT, weight=0.8)`
- `(H2, A1, stance=CONTRADICT, weight=0.9)`

Both rows reference the SAME assertion. No duplication of underlying evidence.

**Current architecture behavior**:
- PASS: `hypothesis_support UNIQUE(hypothesis_id, assertion_id)` — each H+A pair has ONE stance
- PASS: The same assertion can have multiple hypothesis_support rows across DIFFERENT hypotheses
- PASS: This is the core ADR-002 design

**Status**: **PASS**

---

### ADV-26: Officer Changes Role — Historical Access Review
**Scenario**: Supervisor Priya is demoted to INVESTIGATOR after an integrity review. Her access to 12 sealed evidence items should be revoked retroactively.

**Expected**: `civix_user.role` changes from SUPERVISOR to INVESTIGATOR. `case_access` records may need review. `audit_event` shows every access Priya made as SUPERVISOR.

**Current architecture behavior**:
- PASS: `audit_event` captures all access (READ, WRITE, EXPORT) — full historical trail
- PARTIAL: `civix_user.role` is a mutable field. Changing it does not record why or when. There is no role change history.
- **GAP**: No `civix.user_role_history` table or `tx_start/tx_end` on `civix_user`. Role history is an audit gap.

**Status**: **PARTIAL** — role change is not auditable.

---

### ADV-27: Property Transfer References Non-Existent Property Entity
**Scenario**: Ingesting PROP-TX-000001 (Khasra 45 sold by P-14 to P-12). But Khasra 45 does not yet exist as a `civix.property` entity. The event references a property that hasn't been created yet.

**Expected**: Ingestion should create the `civix.property` entity first, then create the event and event_participants.

**Current architecture behavior**:
- PASS: `event_participant.entity_id FK→entity` means the property entity MUST exist before the participant row can be inserted (FK constraint)
- PASS: This forces the correct ordering: create property entity first
- **GAP**: The ingestion pipeline order is critical. The documentation does not define the exact ingestion ordering for property-transfer events. If the pipeline processes events in CSV order without first ensuring property entities exist, FK violations will occur.

**Status**: **PARTIAL** — constraint enforces ordering but ingestion pipeline order is undocumented.

---

### ADV-28: GPS Spoofing — Vehicle Appears in Two Locations Simultaneously
**Scenario**: Two CDRs report vehicle RJ14CD5678 at CELL-01 (Ajmer East) at 14:30 AND CELL-47 (Ajmer West, 30km away) at 14:31. This is physically impossible within 1 minute.

**Expected**: Both source_records are ingested. Both events are created. A `data_quality_issue(SPATIAL_IMPOSSIBILITY)` is created. Neither record is deleted. The impossibility is flagged for human review.

**Current architecture behavior**:
- PASS: `data_quality_issue_type_enum` includes `SPATIAL_IMPOSSIBILITY`
- PASS: Both CDRs create separate event records — no auto-deduplication
- PASS: Human-reviewed — no automatic assertion rejection
- **GAP**: There is no automated spatial impossibility detection at ingestion time. The `data_quality_issue` must be created by application logic that checks speed-of-travel constraints. This logic is not defined anywhere in the architecture documents.

**Status**: **PARTIAL** — DQI type exists but detection logic undefined.

---

### ADV-29: Observation Made by Anonymous Officer
**Scenario**: A surveillance observation (SURV-000001) says `"observing_officer": "Constable Vijay Kumar (P-28)"`. But in another case, a surveillance report says `"observing_officer": "Confidential"` — the officer's identity is protected for safety.

**Expected**: The anonymous observation has `observer_entity_id=NULL` and `observation_text` describes what was observed without naming the observer. The source is protected.

**Current architecture behavior**:
- PASS: `observation.observed_by` is NULLABLE
- PASS: `source.is_identity_protected=TRUE` protects the SOURCE (informant), not the observer
- **GAP**: If the observing officer wants anonymity (not the informant, but the actual officer who conducted surveillance), there is no mechanism to anonymize the observer while maintaining the observation record. The current design either names the officer or puts NULL.
- **GAP**: The proposed BLK-13 (`observer_entity_id`) makes this worse — you'd have a FK to an entity that should be hidden. If the entity is hidden via legal restriction, the observation becomes orphaned from its observer.

**Status**: **PARTIAL** — anonymous observer scenario partially handled.

---

### ADV-30: Assertion With NULL object_entity_id AND NULL object_value [CRITICAL DB TEST]
**Scenario**: Application code bug creates an assertion with no valid object. All three object columns are NULL: `object_entity_id=NULL`, `object_value=NULL`, `object_location_id=NULL`.

**Expected**: DB CHECK constraint rejects the insert.

**Current architecture behavior**:
- PASS: `CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL OR object_location_id IS NOT NULL)` rejects this
- After BLK-17 fix (removing `object_location_id`): The 2-way check `CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL)` still rejects this.
- **Note**: What about `predicate=TIME_OF_DEATH_IS` with `object_value='2026-08-13 14:30'`? This requires `object_value` to be a free-text timestamp. Consider whether time-of-death should reference a temporal range rather than a text string.

**Status**: **PASS**

---

## Summary Table

| Test | Scenario | Status |
|---|---|---|
| ADV-01 | Father/son same name | PARTIAL |
| ADV-02 | Phone number reuse (handset resale) | PASS |
| ADV-03 | SIM in two devices same day | PARTIAL |
| ADV-04 | Identity merge then disagreeing expert | PASS |
| ADV-05 | Unresolved person in CCTV | PARTIAL |
| ADV-06 | Same evidence in three cases | PASS |
| ADV-07 | Valid alibi contradicts hypothesis | PASS |
| ADV-08 | Duplicate CCTV from two cameras | PASS |
| ADV-09 | Unknown financial counterparty | PARTIAL |
| ADV-10 | Multi-hop property fraud | PASS |
| ADV-11 | Late-arriving evidence | PASS |
| ADV-12 | Historical ML feature leakage | PASS |
| ADV-13 | Time window uncertainty | PASS |
| ADV-14 | Compromised source, 5000 records | PARTIAL |
| ADV-15 | Chain of custody gap | FAIL (MVP) |
| ADV-16 | Conflicting lab results | FAIL (MVP) |
| ADV-17 | Officer transfer mid-case | PARTIAL |
| ADV-18 | Sealed evidence, lead still visible | PARTIAL |
| ADV-19 | Assertion cross-case access | FAIL |
| ADV-20 | Expunged entity downstream effects | PARTIAL |
| ADV-21 | AI extracts nonexistent entity | PARTIAL |
| ADV-22 | AI analysis run found faulty | FAIL |
| ADV-23 | Low-confidence OCR creates bad extraction | PARTIAL |
| ADV-24 | Community detection implicates innocent | PARTIAL |
| ADV-25 | Same assertion in competing hypotheses | PASS |
| ADV-26 | Officer role change — audit | PARTIAL |
| ADV-27 | Property transfer references missing property | PARTIAL |
| ADV-28 | GPS spoofing — spatial impossibility | PARTIAL |
| ADV-29 | Anonymous observer | PARTIAL |
| ADV-30 | Assertion with all-null object columns | PASS |

**PASS: 9** | **PARTIAL: 16** | **FAIL: 5**

> [!CAUTION]
> ADV-19 (assertion cross-case access) and ADV-22 (analysis run invalidation) are FAIL with HIGH impact.
> These must be addressed before Phase 3 begins.

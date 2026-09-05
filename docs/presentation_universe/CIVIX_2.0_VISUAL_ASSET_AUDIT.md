# CIVIX 2.0 — PRESENTATION EVIDENCE VISUAL ASSET PREFLIGHT AUDIT

## STEP 1 — INVENTORY THE 240 ITEMS (Seeded)
Based on `seed_12case_universe.py`, there are exactly 240 items seeded across the 12 Hero cases (20 per case). *(Note: A previous version of this document incorrectly hypothesized a 241st global artifact, which did not exist in the codebase. The canonical count is exactly 240).*

**Inventory Breakdown (Approximate counts per category across all cases):**
- `FIR_DOCUMENT`: 12
- `CALL_DATA_RECORD`: 12+
- `AI_LEAD` / `SYSTEM_ALERT`: ~30
- `FORENSIC_REPORT`: ~15
- `WITNESS_STATEMENT` / `INTERROGATION_TRANSCRIPT`: ~20
- `COURT_ORDER` / `SEIZURE_MEMO` / `MEDICAL_REPORT`: ~30
- `FINANCIAL_STATEMENT` / `PROPERTY_DOCUMENT`: ~15
- `ANPR_DATA`: ~10
- `CCTV_FOOTAGE`: ~10
- **Person Portraits (Mugshots)**: The script seeds 51 deep hero persons, though portraits are assumed metadata rather than direct `evidence_artifact` rows.

*Observation:* The vast majority of the 240 items are textual/structured documents or system UI alerts.

## STEP 2 — CLASSIFY EVERY VISUAL ASSET
- **REAL INTERNET SOURCE:** Generic crime scene contexts, seized cash (CIVIX-010), gold bars (CIVIX-022), generic highway toll plazas (CIVIX-003).
- **GENERATED:** Specific CCTV captures where synthetic suspects are visible, ANPR frames with exact cloned license plates (CIVIX-019), composite sketches, and all Suspect Portraits.
- **EXISTING CIVIX SYNTHETIC ASSET:** System Alerts (CIVIX HERO-04 UI cards), Identity Candidate UI components.
- **NON-VISUAL / DOCUMENT ARTIFACT:** Raw CDRs, Bank Statements, FIR textual data, Court Orders, Transcripts. *These should be rendered natively in the frontend as structured data/text, NOT as AI-generated JPEGs of paper.*

## STEP 3 — INTERNET-SOURCE STRATEGY
- **Preferred Sources:** Wikimedia Commons (CC BY-SA), Unsplash (Open License), Government Open Data Portals (data.gov.in for generic forms).
- **Strategy:** We will acquire generic situational images (e.g., "stack of Indian Rupees", "night highway toll plaza") without any PII or copyright restrictions. Attribution metadata must be stored in `source_record`.

## STEP 4 — FICTIONAL PERSON SAFETY
**Confirmed:** No real internet photographs will be used for any of the 51 synthetic persons (Suspects, Victims, Witnesses). All portraits will be `GENERATED` using Gemini to ensure 100% fictional safety, or reused from `EXISTING_SYNTHETIC` assets.

## STEP 5 — EVIDENCE SEMANTICS
Images will not create unsupported facts. A photo of a Bolero (Real Internet) is merely an `OBSERVATION` linked to the event, not definitive proof. A generated ANPR frame is a `FINDING` derived from the synthetic data generation run, preserving epistemic boundaries.

## STEP 6 — PROVENANCE REQUIREMENTS
The current schema **IS CAPABLE** of representing this cleanly:
- `evidence_artifact` handles `sha256_hash`, `mime_type`, `original_filename`.
- `source_record` can hold the `source_id` (e.g., "WIKIMEDIA_COMMONS"), `external_reference` (URL), and we can store attribution/license in a JSONB metadata field.
- `generation_run` tracks the generated assets.

## STEP 7 — CONTENT-ADDRESSING / HASH AUDIT
Currently, `seed_12case_universe.py` pre-computes deterministic fake hashes (e.g., `hashlib.sha256("civix-evidence-EVD-001-001")`). 
**Gap Identified:** When we actually acquire real images or generate them, the *real* bytes will produce a different SHA-256 hash. The ingestion pipeline MUST update the `evidence_artifact` table with the true hash after the physical bytes are secured.

## STEP 8 — INTERNET IMAGE ACQUISITION RISKS
Required controls for the acquisition script: HTTP timeouts, 404 handling, MIME-type validation (rejecting disguised executables), EXIF stripping, and license tracking.

## STEP 9 — GENERATED IMAGE FALLBACK
For ANPR, specific CCTV, and Portraits:
- **Model Requirement:** Gemini/Imagen 3.
- **Format:** PNG/JPEG.
- **Labeling:** Metadata MUST tag these as `derived/reconstructed`.

## STEP 10 — PERSON PHOTO MANIFEST
- 51 deep hero persons.
- **Recommendation:** Generate 51 synthetic portraits. Ensure `civix.person` records (or linked evidence) properly reference these via true SHA-256 hashes.

## STEP 11 — CASE EVIDENCE MANIFEST
The current flat distribution (exactly 20 per case) is rigid. We will adapt the UI to present meaningful structured data (FIRs, CDRs) natively, reserving visual thumbnails for actual images (CCTV, Forensics). 

## STEP 12 — DATABASE COMPATIBILITY
Fully compatible. No schema changes required.

## STEP 13 — RECOMMENDED ACQUISITION MATRIX (Sample)

| Evidence ID | Case | Evidence Type | Recommended Source | Internet Candidate | Generated Fallback | Provenance Needed | Notes |
|-------------|------|---------------|--------------------|--------------------|--------------------|-------------------|------|
| EVD-001-001 | 001 | FIR_DOCUMENT | NON_VISUAL | N/A | N/A | No | Render as structured text/HTML |
| EVD-001-002 | 001 | CCTV_FOOTAGE | GENERATED | N/A | Imagen 3 | Yes (Run ID) | Needs synthetic person in grey tracksuit |
| EVD-001-004 | 001 | CALL_DATA_RECORD| NON_VISUAL | N/A | N/A | No | Render as data table in UI |
| EVD-001-019 | 001 | AI_LEAD | EXISTING_SYNTHETIC | N/A | N/A | No | UI component rendering |
| EVD-010-002 | 010 | SEIZURE_MEMO(Cash)| REAL_INTERNET | Wikimedia(Rupees)| Imagen 3 | Yes (URL/License)| Generic stack of cash |
| EVD-019-001 | 019 | ANPR_DATA | GENERATED | N/A | Imagen 3 | Yes (Run ID) | Needs exact plate DL-8C-AB-1234 |
| PORTRAIT-01 | ALL | PERSON_PORTRAIT | GENERATED | N/A | Imagen 3 | Yes (Run ID) | Fictional safety critical |

## STEP 14 — THREE-ASSET PILOT DESIGN

1. **Internet-Sourced:** Generic Seized Cash (CIVIX-010)
   - *Flow:* Source Wikimedia CC-BY -> Download -> Validate MIME -> Strip EXIF -> Compute True SHA-256 -> Update `evidence_artifact` -> Stored in `/evidence_store`.
2. **Existing Synthetic:** CIVIX HERO-04 Biometric Alert
   - *Flow:* Render UI component -> Export as PNG -> Compute SHA-256 -> Register.
3. **Generated Asset:** ANPR Hit for DL-8C-AB-1234 (CIVIX-019)
   - *Flow:* Prompt Imagen -> Validate bytes -> Compute True SHA-256 -> Update `evidence_artifact` -> Tag as `synthetic/reconstructed`.

---
*Audit Complete.*

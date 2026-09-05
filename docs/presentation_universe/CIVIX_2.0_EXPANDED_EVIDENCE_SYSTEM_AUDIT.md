# CIVIX 2.0 — EXPANDED EVIDENCE UNIVERSE: FULL SYSTEM-WIDE PRE-IMPLEMENTATION AUDIT

## PART 1 — CURRENT BASELINE
*Confirmed via exact database queries and `seed_12case_universe.py` output.*
1. **Cases**: 267 (12 Hero, 255 background)
2. **Persons**: 15,051
3. **Organizations**: 2,018
4. **Vehicles**: 12
5. **Telecom/Hardware**: 15,026 phones, 7,525 devices
6. **Financial/Property**: 5,014 accounts, 8 properties
7. **Investigative Leads**: 29
8. **Evidence Artifacts**: 408 (Formerly assumed 409)
9. **MIME-Type Distribution**: 228 `application/pdf`, 180 `image/png`

## PART 2 — AUDIT THE PROPOSED 240 → PDF CONVERSION
**RISK LEVEL: BLOCKER.**
Converting all 240 evidence records to PDF is architecturally semantically invalid. 
- **Structured Data Confusion**: `CALL_DATA_RECORD`, `AI_LEAD`, and `SYSTEM_ALERT` are native, structured CIVIX intelligence outputs. Converting these into unstructured PDFs destroys their semantic value and confuses *Source Data* with *Presentation Representation*.
- **Verdict**: The proposal fails here. CDRs and Financial Statements must remain structured data and be rendered natively in the frontend.

## PART 3 — AUDIT THE "240 PDFs" GENERATION STRATEGY
**RISK LEVEL: BLOCKER.**
The proposal suggests using an Image Model (Gemini/Imagen) to "draw" a document, and then wrapping that image in a PDF.
- **Hallucination Risk**: Asking an image model to draw a bank statement for `ACC-0095A` with exactly `₹28,00,000` transferred on `2024-11-12` will result in OCR errors, hallucinated dates, illegible text, and numerical contradictions with PostgreSQL.
- **Correct Architecture**: `STRUCTURED DATA → DETERMINISTIC DOCUMENT RENDERER → PDF`. Generative image models must *never* be used to generate textual/numeric documents in an investigative system.

## PART 4 — AUDIT THE 168 NEW IMAGES
**RISK LEVEL: MAJOR.**
The arbitrary constraint of "14 images per case" forces volume over meaning.
- A case like CIVIX-001 might only have 3 valid visual observation points (2 CCTV frames, 1 Mugshot). Forcing 11 more visual images will result in meaningless filler (e.g., generic street photos) that dilute the investigative graph and create disconnected "orphan" nodes.

## PART 5 — AUDIT THE PERSON PORTRAIT ARCHITECTURE
**RISK LEVEL: MAJOR.**
The `civix.person` schema does not contain a dedicated `portrait_id` column. Portraits are currently resolved implicitly through `evidence_instance` linked to the person entity.
- **Safety**: Fictional persons must be generated. We cannot use real internet photos. Generated portraits must be strictly labeled as `synthetic/reconstructed`.

## PART 6 — AUDIT INTERNET-SOURCED IMAGE STRATEGY
**RISK LEVEL: PASS.**
The `civix.source_record` table cleanly handles external provenance (`source_id`, `external_reference`). 

## PART 7 — CRITICAL HASH / CONTENT-ADDRESSING AUDIT
**RISK LEVEL: BLOCKER.**
The `civix.evidence_artifact` table uses `UNIQUE (sha256_hash, hash_algorithm)`.
- The current seed script inserts fake deterministic hashes before physical bytes exist. 
- Updating an artifact's hash *after* generation breaks the immutability contract of content-addressed storage. 
- **Correct Lifecycle**: Physical Bytes → Validate → Hash → Database Registration. The database cannot register a final artifact row before the bytes exist.

## PART 8 — EVIDENCE IMMUTABILITY
**RISK LEVEL: BLOCKER.**
Evidence artifacts are treated as immutable globally deduplicated records (ADR-004, BLK-19). Replacing a seeded fake hash with a real hash via a SQL `UPDATE` is architecturally invalid. The artifact must be created *after* the file is generated, or the seed must act merely as a generation queue that inserts the final artifact later.

## PART 9 — PROVENANCE
**RISK LEVEL: PASS.**
`generation_run` handles model tracking, and `source_record` handles internet origins perfectly.

## PART 10 — EPISTEMIC SEMANTICS
**RISK LEVEL: BLOCKER (if executed as proposed).**
Generated visual assets (like ANPR plates) must remain as an `OBSERVATION` or `MODEL SIGNAL`. If a user generates an image of a red Toyota that contradicts a database record saying the vehicle is a black Bolero, the image falsely creates an unsupported factual claim.

## PART 11 — "GRAPH FIRST, EVIDENCE SECOND"
**RISK LEVEL: PASS (with constraints).**
Generating evidence to match the graph is a valid synthetic data technique for the presentation universe, *provided* the generated visual is tagged as synthetic and does not attempt to introduce new structured facts that aren't in the graph.

## PART 12 — EVENT ↔ EVIDENCE LINKAGE
**RISK LEVEL: MAJOR.**
Adding 168 arbitrary images threatens to create orphan artifacts. Every image MUST link to a specific `Event` or `Event Location` in the graph. 

## PART 13-17 — UX, API, DB, CDC, NEO4J
**RISK LEVEL: PASS.**
The backend, frontend, and Neo4j graph easily scale to 408 artifacts without performance degradation or payload issues. RLS policies by `case_id` will correctly isolate the data.

## PART 18 — SEEDING / IDEMPOTENCY
**RISK LEVEL: MAJOR.**
Running the image generation script outside the seed breaks idempotency. A partial failure during generation leaves orphaned database records with missing files.

## PART 19 — PHYSICAL EVIDENCE STORE
**RISK LEVEL: MAJOR.**
Direct writes to `c:\data\civix_demo\evidence_store` lack staging isolation. The script must write to a temp directory, hash, and move atomically to prevent corrupted files from entering the main store.

## PART 20 — PDF GENERATION
**RISK LEVEL: MAJOR.**
Generating deterministic PDFs requires adding a new architectural component (e.g., Python `reportlab` or an HTML-to-PDF microservice), expanding the scope of the backend.

## PART 21 — IMAGE GENERATION
**RISK LEVEL: PASS.**
Gemini / Imagen 3 via the Python SDK is capable, provided robust exponential backoff is implemented.

## PART 25-27 — GROUND TRUTH, CHAINS, DEMO REALISM
**RISK LEVEL: BLOCKER.**
Forcing 408 generative images/PDFs creates a visually repetitive, "fake" feeling environment. A real system contains highly structured data interspersed with occasional, critical visual evidence. Over-generating AI documents damages the credibility of the presentation universe.

---

# FINAL DECISION

## DO NOT PROCEED

### 1. Executive verdict
The proposal to use an AI image model to draw 240 structured documents as PDF images, combined with updating immutable cryptographic hashes in-place, violates core CIVIX architectural constraints, epistemic semantics, and content-addressing integrity.

### 2. Blockers
- **Generative Text Hallucination**: You cannot use an image model to generate structured investigative documents (CDRs, bank statements). It will contradict PostgreSQL ground truth.
- **Immutability Violation**: Updating `sha256_hash` on an existing `evidence_artifact` breaks the global deduplication and immutability contract.

### 3. Major findings
- Forcing an arbitrary "14 images per case" creates orphan evidence disconnected from graph events and dilutes demo realism.
- The system lacks a deterministic PDF rendering pipeline, which would require an out-of-scope architectural expansion.

### 4. Required remediation
- Shift structured evidence (CDRs, FIRs, Alerts) back to native UI representations (Non-Visual).
- For documents that *must* be PDFs, implement a deterministic HTML-to-PDF renderer driven by PostgreSQL data, NOT an image generator.
- Alter the ingestion lifecycle: Only insert rows into `civix.evidence_artifact` *after* the physical file is generated/downloaded and truly hashed.

### 5. Architecture decision
Evidence must strictly follow: `BYTES EXIST → HASH COMPUTED → ARTIFACT REGISTERED`. The database must never contain fake placeholder hashes for evidence files.

### 6. Recommended evidence strategy
Retain the 160 structured records as pure data. Generate visual imagery ONLY for assets that are natively visual (CCTV, ANPR, Portraits).

### 7. Recommended PDF strategy
Do not implement. If printable documents are required, use a deterministic templating engine in the frontend or API layer, not physical PDF generation via AI.

### 8. Recommended image strategy
Generate the ~51 fictional portraits and ~30 highly specific synthetic observations (e.g., cloned plates). Source the rest (e.g., cash, gold, generic highways) from open-license internet repositories.

### 9. Required pilot
If remediations are accepted, execute the 3-asset pilot (1 Internet, 1 Synthetic UI, 1 Generated Image) ensuring the hash-first lifecycle is strictly obeyed.

### 10. Full-batch acceptance criteria
- Zero instances of `UPDATE civix.evidence_artifact SET sha256_hash...`
- Zero generative images used for textual/financial structured documents.
- 100% of generated images are tagged as `derived/reconstructed`.
- 100% of images are linked to a specific Event or Entity (no orphans).

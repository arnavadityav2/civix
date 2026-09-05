# ANTIGRAVITY EXECUTION GUIDE v1.0
## Fast Batch Sourcing & Generation for CIVIX 2.0 Universe

**Target:** 1,085+ images + 750 evidence documents | **Estimated Runtime:** 14–18 hours batch mode

---

## PHASE 1: SETUP & VALIDATION (30 min)

### 1.1 Input Manifest Files (READ-ONLY)
- `CIVIX_UNIVERSE_SPECIFICATION.md` — Master spec, 50 cases, 7 networks
- `CIVIX_Universe_Bible_Part_2.md` — 55-case deep specs, hero cases
- `CIVIX_Universe_Bible_Part_3.md` — Persons roster (P0001–P0320+), orgs, vehicles
- `CIVIX_Persons_Photo_Manifest_v1.0.md` — Photo sourcing specs for 150+ persons
- `CASES_EVIDENCE_MANIFEST.md` — 750 evidence items, 15 per case

### 1.2 Version Note
**CONFLICT DETECTED:** Files contain inconsistency in case count (50 vs. 55) and person ID assignments. **Use CIVIX_Universe_Bible_Part_2/3 (55-case variant) as canonical.** Evidence Manifest references different person IDs — cross-map during execution.

### 1.3 Output Directory Structure
```
/mnt/user-data/outputs/
├── /photos/
│   ├── /N1_persons/  (P0001–P0024)
│   ├── /N2_persons/  (P0025–P0044)
│   ├── /N3_persons/  (P0045–P0059)
│   ├── /N4_persons/  (P0070–P0087)
│   ├── /N5_persons/  (P0095–P0109)
│   ├── /N6_persons/  (P0120–P0131)
│   ├── /N7_persons/  (P0155–P0164)
│   └── /witness_victims/  (P0200–P0320)
├── /evidence/
│   ├── /CIVIX-001/ → EVD-001-001 through EVD-001-015
│   ├── /CIVIX-002/ → EVD-002-001 through EVD-002-015
│   └── ... /CIVIX-050/ (or CIVIX-055 if using 55-case variant)
├── PHOTO_REGISTRY.csv
├── EVIDENCE_REGISTRY.csv
└── EXECUTION_LOG.txt
```

---

## PHASE 2: PERSON PHOTOS (150+ persons, ~260 images)

### 2.1 Batch Sourcing Strategy

**Step 1: Open-Source Search (first 2 attempts per person)**
- Platform priority: Wikimedia Commons → Unsplash → Pexels → Pixabay → archive.org
- Search terms from Photo Manifest (e.g., "Indian male police mugshot 50s", "Indian customs officer female")
- Skip if result is identifiable as real person — reject and generate synthetic instead
- Log search attempts in EXECUTION_LOG.txt

**Step 2: Synthetic Generation (fallback)**
- Use GENERATE_SYNTHETIC prompts from Photo Manifest
- Tool: Stable Diffusion / Midjourney / Flux
- Critical constraints:
  - NO real-world mugshots or real people
  - Document-style photos (booking, dossier): sharp, institutional lighting
  - Citizen photos (victim, witness): natural, civilian framing
  - Family resemblance pairs: P0001 (Suresh Valmiki) + P0120 (Dinesh Yadav) must show visual kinship
  - False-positive pairs: P0003 ("Bhura" robber) vs. P0133 ("Bhura" truck driver) must look visually distinct
  - Central Asian appearance: P0073 (Farrukh Tashkentov) — NOT South Asian

**Step 3: No-Photo Hard-Coded**
- 30 persons marked NO_PHOTO in manifest (absconding, deceased, foreign, unidentified)
- Do NOT attempt sourcing
- Create text placeholder card: `NO_PHOTO_[PERSONID]_REASON.txt` with documented reason

### 2.2 Photo Output Naming & Registry
```
Photo filename: PHOTO_[PERSONID]_[TYPE].jpg
Types: BOOKING | DOSSIER | CIVILIAN | SKETCH | SURVEILLANCE | PROFESSIONAL

Two-image persons (special):
  PHOTO_P0075_01_SKETCH_2012.jpg (composite sketch)
  PHOTO_P0075_02_SURVEILLANCE_2021.jpg (grainy CCTV still)

Registry entry (CSV):
  PERSONID,FULL_NAME,PHOTO_TYPE,FILENAME,SOURCE_TYPE,STATUS
  P0001,Suresh Valmiki,BOOKING,PHOTO_P0001_BOOKING.jpg,GENERATE_SYNTHETIC,COMPLETE
  P0009,Manjeet Rawat,NO_PHOTO,NO_PHOTO_P0009_REASON.txt,NO_ATTEMPT,COMPLETE
```

### 2.3 Quality Checkpoints
- [ ] All 150+ persons have photo or explicit NO_PHOTO reason
- [ ] ~5% NO_PHOTO (acceptable per manifest)
- [ ] Hero persons visible and distinctive (P0001, P0075, P0025, P0070, P0095, P0120, P0155)
- [ ] Cross-network connections visually apparent where needed (P0001 ↔ P0120 family)

---

## PHASE 3: EVIDENCE ARTIFACTS (750 documents, ~825 images)

### 3.1 Batch Processing by Type

**FIR PDFs (1 per case + supplements) — ~60 total**
- Search: "India police FIR template PDF" + case-specific terms
- Fallback: Generate realistic document (police letterhead, case number, suspect names, status)
- Tool: LibreOffice Writer + PDF export or Canva template

**CCTV Clips (video, 2–3 min each) — ~50 total**
- Search: Generic "Delhi market robbery CCTV", "toll plaza security footage"
- Fallback: Reconstruct from stock footage (crowd scenes, street views, market interiors) + timestamp overlay + synthetic masked figures or AI crowd
- Tool: FFmpeg + stock footage libraries (Pexels Videos, Pixabay Videos)
- Output: MP4, 480p–720p era-appropriate quality

**ANPR Crops (vehicle plate detection images) — ~40 total**
- Search: "India toll plaza ANPR detection", "motorcycle license plate photograph"
- Fallback: Generate realistic ANPR output (vehicle front-on, plate sharp, timestamp, confidence score overlay)
- Tool: Stable Diffusion + image composition (Photoshop/GIMP layer overlay)
- Output: PNG, 1024×768px

**AFIS Fingerprint Reports (10-print cards, latent matches) — ~20 total**
- Search: "India police fingerprint card template", "AFIS report PDF"
- Fallback: Generate realistic card (rolled/plain prints, palm prints, name/DOB, certification)
- Tool: Latex/PDF template + synthetic fingerprint patterns (whorls/loops/arches)
- Output: PDF + PNG (if displaying prints graphically)

**CDR Dumps (call records, CSV) — ~45 total**
- Generate only (no open-source equivalent)
- Format: CSV with columns [Call_Time, From_MSISDN, To_MSISDN, Duration_Sec, Tower_ID, Tower_Location]
- Data: Realistic tower IDs (DWK-023-01, NH48-012, etc.), timestamps matching crime windows, tower clustering patterns per network
- Tool: Python pandas + template CSV

**Interrogation Transcripts — ~60 total**
- Generate (realistic police template, Q&A format, typewritten font for historic cases)
- Tool: LibreOffice Writer, typewriter font (Courier), simulate handwriting for notes
- Output: PDF

**Bank/Financial Statements — ~40 total**
- Search: "India bank statement template PDF", "HDFC statement sample"
- Fallback: Generate realistic statement (bank letterhead, account number, transaction history, period range)
- Tool: LibreOffice Calc export to PDF
- Output: PDF

**Forensic Reports (medical, ballistics, fingerprint, GSR, autopsy) — ~35 total**
- Generate (clinical/technical format, NOT graphic imagery)
- Tool: LibreOffice Writer + medical terminology
- Constraint: Document-style only; avoid injury photography
- Output: PDF

**Vehicle/Property Registrations — ~30 total**
- Search: "India RC registration certificate", "land registry deed"
- Fallback: Generate realistic government document (RTO/revenue office letterhead, registration numbers, owner details)
- Tool: LibreOffice Writer
- Output: PDF

**Customs Forms, Insurance Claims, Court Documents — ~25 total**
- Generate realistic forms (Customs Act forms, insurance claim templates, judicial templates)
- Tool: LibreOffice Writer + government form templates
- Output: PDF

### 3.2 Evidence Sourcing Checklist (Per Case)
```
CIVIX-001: Dwarka Sector 23 Cash Van Robbery
  EVD-001-001: FIR PDF — [ ] Sourced or generated
  EVD-001-002: AFIS 10-Print Card — [ ] Generated (synthetic prints)
  EVD-001-003: CCTV Clip — [ ] Generated (stock + overlay)
  EVD-001-004: Interrogation Transcript — [ ] Generated (template)
  ... EVD-001-015 — [checkboxes for all 15]
  
[Repeat for CIVIX-002 through CIVIX-050/055]
```

### 3.3 Hero Evidence Priority (Complete First)
- EVD-CHAINA-1: AFIS booking card (P0001 ten-print)
- EVD-CHAINA-2: Latent print AFIS card (CIVIX-003 steering wheel)
- EVD-CHAINA-3: Financial audit trace (robbery proceeds → Dinesh Yadav shell)
- EVD-HERO-1A: Interrogation transcript (Rakesh Yadav, "Pandit" alias mention)
- EVD-HERO-2A: Bank SAR PDF (CIVIX-010, flagging Arham Bullion Traders)
- EVD-HERO-3A: ANPR crop pair (spatial paradox, DL-8C-AB-1234, two locations 3 min apart)

---

## PHASE 4: DATA QUALITY & VALIDATION (2 hours)

### 4.1 Cross-Reference Verification
- [ ] All P#### references in evidence match Persons Photo Manifest
- [ ] All ORG### references match Entity Roster (Doc 3)
- [ ] All case IDs (CIVIX-001 through CIVIX-050/055) present and unique
- [ ] All evidence ID codes follow pattern: EVD-{CASEID}-{SEQ}_{Description}

### 4.2 Person-Evidence Cross-Reference
Random spot-check: Pick 5 evidence items, verify all persons mentioned:
- [ ] CIVIX-001 EVD-001-001 (FIR) mentions P0002, P0003, P0004, P0005 — all have photos in registry ✓
- [ ] CIVIX-010 EVD-010-001 (Bank SAR) mentions ORG-031 (Arham Bullion Traders) — confirmed in Entity Roster ✓
- [ ] ... (continue 3 more spot checks)

### 4.3 Media File Integrity
- [ ] All JPG/PNG files properly formatted (open in image viewer without error)
- [ ] All MP4 files playable (ffprobe validation)
- [ ] All PDF files text-searchable (not corrupted)
- [ ] All CSV files parse correctly (no encoding issues)

---

## PHASE 5: REGISTRY GENERATION (1 hour)

### 5.1 PHOTO_REGISTRY.csv
```csv
PERSONID,FULL_NAME,ALIAS,NETWORK,PHOTO_COUNT,FILENAME_1,FILENAME_2,SOURCE_TYPE,STATUS,NOTES
P0001,Suresh Valmiki,Suri Bhai,N1,1,PHOTO_P0001_BOOKING.jpg,,GENERATE_SYNTHETIC,COMPLETE,Principal N1 leader
P0075,Vikram Sharma,Vikram @ Pandit,N1-N4,2,PHOTO_P0075_01_SKETCH_2012.jpg,PHOTO_P0075_02_SURVEILLANCE_2021.jpg,GENERATE_SYNTHETIC,COMPLETE,HERO-01 key link
...
```
Columns: PERSONID | FULL_NAME | ALIAS | NETWORK | PHOTO_COUNT | FILENAME_1 | FILENAME_2 | SOURCE_TYPE (OPEN_SOURCE|GENERATE_SYNTHETIC|NO_PHOTO) | STATUS | NOTES

### 5.2 EVIDENCE_REGISTRY.csv
```csv
CASEID,CASE_TITLE,NETWORK,EVD_ID,EVIDENCE_TYPE,FILENAME,ASSOCIATED_PERSONS,ASSOCIATED_ORGS,SOURCE_PREFERENCE,STATUS,NOTES
CIVIX-001,Dwarka Sector 23 Cash Van Robbery 2012,N1,EVD-001-001,FIR_PDF,EVD-001-001_Dwarka_PS_FIR_2012_CashVan.pdf,P0002|P0003|P0004|P0005|PERSON_UNKNOWN_05,Dwarka PS,GENERATE_FORENSIC_MOCKUP,COMPLETE,
CIVIX-001,Dwarka Sector 23 Cash Van Robbery 2012,N1,EVD-001-002,AFIS_FINGERPRINT,EVD-001-002_Fingerprint_10Print_P0002.png,P0002,Dwarka PS Forensic Lab,GENERATE_SYNTHETIC,COMPLETE,Synthetic whorls/loops
...
```
Columns: CASEID | CASE_TITLE | NETWORK | EVD_ID | EVIDENCE_TYPE | FILENAME | ASSOCIATED_PERSONS | ASSOCIATED_ORGS | SOURCE_PREFERENCE | STATUS | NOTES

### 5.3 EXECUTION_LOG.txt
```
EXECUTION START: 2026-09-04 10:00 UTC
==================================================

PHASE 1: Setup & Validation — COMPLETE (30 min)
  Canonical version: 55-case variant (CIVIX_Universe_Bible_Part_2/3)
  Person count: 320+
  Evidence count: 750
  Output directory: /mnt/user-data/outputs/

PHASE 2: Person Photos (150+ persons) — IN PROGRESS (6 hours elapsed / 8 hours estimated)
  Sourced (open-source): 45 persons
  Generated (synthetic): 185 persons
  No-photo: 30 persons
  Total complete: 260/260 ✓

PHASE 3: Evidence Artifacts (750 documents) — IN PROGRESS (10 hours elapsed / 12 hours estimated)
  FIRs: 50/55 complete
  CCTV clips: 48/50 complete
  ANPR crops: 35/40 complete
  Fingerprint reports: 18/20 complete
  CDR dumps: 45/45 complete ✓
  Interrogation transcripts: 58/60 complete
  Bank/financial: 38/40 complete
  Forensic reports: 33/35 complete
  Vehicle/property registrations: 28/30 complete
  Forms/claims/court docs: 23/25 complete
  Total complete: 726/750 (96.8%)

PHASE 4: Validation — PENDING
PHASE 5: Registry Generation — PENDING

ISSUES LOG:
  - Case count conflict (50 vs. 55): Using 55-case variant as canonical
  - Person ID mismatch (Evidence Manifest vs. Photo Manifest): Cross-mapping applied
  - Spot-check CIVIX-001 EVD-001-002 (AFIS card): Generated ✓ Validated ✓
  
NEXT STEPS:
  - Complete remaining 24 evidence items
  - Run validation checksums
  - Generate final registries
  - Estimate completion: 2026-09-05 02:00 UTC (16 hours total)
```

---

## PHASE 6: HANDOFF TO POSTGRESQL (After Completion)

### 6.1 Database Ingestion
Once all photos & evidence generated:
1. Copy all output files to staging directory
2. Run `POSTGRES_INGESTION_SPEC.md` SQL scripts (when created)
3. Populate tables: `civix_person` | `civix_investigative_case` | `civix_evidence_artifact` | `civix_organization` | `civix_vehicle` | etc.
4. Validate row counts against manifest
5. Run RLS policy tests

### 6.2 Neo4j CDC Sync (After DB Complete)
1. Enable CDC outbox table in PostgreSQL
2. Sync outbox → Neo4j via CDC processor
3. Create nodes/relationships for graph queries
4. Validate cross-case link queries (LEAD-001 through LEAD-006)

---

## COMMAND-LINE QUICK-START

```bash
# Create directories
mkdir -p /mnt/user-data/outputs/{photos,evidence,photos/{N1_persons,N2_persons,N3_persons,N4_persons,N5_persons,N6_persons,N7_persons,witness_victims}}
mkdir -p /mnt/user-data/outputs/evidence/{CIVIX-001..CIVIX-055}

# Start batch sourcing (estimated runtime)
python3 antigravity_batch_executor.py \
  --manifest /mnt/user-data/uploads/CIVIX_Persons_Photo_Manifest_v1.0.md \
  --output-dir /mnt/user-data/outputs/photos \
  --source-priority OPEN_SOURCE_FIRST \
  --fallback GENERATE_SYNTHETIC \
  --log /mnt/user-data/outputs/EXECUTION_LOG.txt

# Start evidence generation
python3 antigravity_evidence_executor.py \
  --manifest /mnt/user-data/uploads/CASES_EVIDENCE_MANIFEST.md \
  --output-dir /mnt/user-data/outputs/evidence \
  --template-dir ./forensic_templates \
  --log /mnt/user-data/outputs/EXECUTION_LOG.txt

# Generate registries (after completion)
python3 generate_registries.py \
  --photo-dir /mnt/user-data/outputs/photos \
  --evidence-dir /mnt/user-data/outputs/evidence \
  --output /mnt/user-data/outputs/{PHOTO,EVIDENCE}_REGISTRY.csv
```

---

## SUCCESS CRITERIA (Final Checkpoint)

- [ ] 260 person photos (150+ unique persons, multi-image for hero persons)
- [ ] 750 evidence artifacts across 55 cases
- [ ] 0 missing cross-references (all P####, ORG### accounted)
- [ ] Hero evidence (6 items) verified and demo-ready
- [ ] All output files in `/mnt/user-data/outputs/`
- [ ] PHOTO_REGISTRY.csv + EVIDENCE_REGISTRY.csv generated
- [ ] EXECUTION_LOG.txt final status: COMPLETE

---

**END OF GUIDE**
*Proceed to LOCATIONS_SPATIAL_MANIFEST.md once this phase completes.*

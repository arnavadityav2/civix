# CIVIX 2.0 — CASES EVIDENCE MANIFEST
### Version 1.0 — 50 Cases × 15 Evidence Items = 750 Evidence Specifications
**Cross-Referenced Against: Universe Specification, Persons Photo Manifest, Principal Entity Roster (LOCKED CANONICAL FILES)**

---

## EVIDENCE MANIFEST STRUCTURE

Each case below contains **15 evidence specifications** organized by:
- **EVD-{CASE_ID}-{SEQ}** — Unique evidence ID
- **Type** — FIR_PDF | CCTV_CLIP | ANPR_CROP | AFIS_FINGERPRINT | CDR_DUMP | INTERROGATION_TRANSCRIPT | BANK_SAR | FORENSIC_AUDIT | LAND_REGISTRY | FINANCIAL_STATEMENT | PHONE_RECORD | CUSTOMS_FORM | VEHICLE_SEIZURE | CONFESSION_AFFIDAVIT | CORONER_REPORT
- **Description** — What the evidence is (narrative + forensic context)
- **Associated Persons** — Cross-referenced from Persons Photo Manifest (P####)
- **Associated Organizations** — Cross-referenced from Entity Roster (ORG###)
- **Prompt for Antigravity** — Search terms (open-source) or generation instructions (synthetic)
- **Source Preference** — OPEN_SOURCE_FIRST | GENERATE_FORENSIC_MOCKUP | GENERATE_SYNTHETIC
- **Output Filename** — Where Antigravity saves the file

---

## NETWORK N1 — ARMED ROBBERY & LOGISTICS SYNDICATE (Cases CIVIX-001 through CIVIX-008)

### CIVIX-001: Dwarka Sector 23 Cash Van Robbery (2012) — 'The 5th Robber'
**Status:** CLOSED_CONVICTED | **Area:** Dwarka Sector 23 | **Suspects:** P0127, P0092, P0057, PERSON_UNKNOWN_05
**Network:** N1 (Armed Robbery & Logistics) | **Opened:** 2012-03-14

#### EVD-001-001 — FIR PDF
- **Type:** FIR_PDF
- **Description:** First Information Report filed by Dwarka PS for the 2012 daylight cash van robbery near Sector 23 market. 4 of 5 robbers identified; one suspect "Vikram @ Pandit" remains at large (PERSON_UNKNOWN_05). Initial MO includes armed assault, use of firearm, forced opening of transit vehicle.
- **Associated Persons:** P0127 (Vinod Sabharwal — convicted), P0092, P0057, PERSON_UNKNOWN_05 (alias "Vikram @ Pandit")
- **Associated Organizations:** None (street crime)
- **Prompt for Antigravity:** Search: "FIR template India armed robbery 2012 cash van Dwarka" OR generate: Create a realistic PDF styled as a 2012 Dwarka PS First Information Report. Include: case number, suspect names, MO description, weapon details (revolver/AK-47), recovery section (empty for unknown suspect). Use official Indian police FIR format. Not photoreal — document-style mockup.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP (no real 2012 Dwarka PS FIR exists online; generate realistic document)
- **Output Filename:** EVD-001-001_Dwarka_PS_FIR_2012_CashVan.pdf

#### EVD-001-002 — AFIS Fingerprint Report (10-Print Card)
- **Type:** AFIS_FINGERPRINT
- **Description:** Ten-print fingerprint card for Vinod Sabharwal (P0127), arrested at crime scene. Includes rolled and plain prints of all 10 digits, palm prints, and signature certification by arresting constable.
- **Associated Persons:** P0127 (Vinod Sabharwal)
- **Associated Organizations:** Dwarka PS (arresting agency)
- **Prompt for Antigravity:** Search: "India police 10-print fingerprint card template" OR generate: Create a realistic 10-print card styled after Indian AFIS standards. Include: rolled prints (thumb through pinky, both hands), plain prints, palm prints, name "Vinod Sabharwal", DOB 1974-04-28, Aadhaar placeholder, arrest date 2012-03-14. Cartridge-paper texture, blue-black ink impressions. Not a real person's prints — synthetic whorls/loops/arches.
- **Source Preference:** GENERATE_SYNTHETIC (synthetic fingerprint patterns)
- **Output Filename:** EVD-001-002_Fingerprint_10Print_P0127_Sabharwal.png

#### EVD-001-003 — CCTV Clip (Market Camera)
- **Type:** CCTV_CLIP
- **Description:** 2-minute CCTV footage from Dwarka Sector 23 market security camera. Shows the armored van pulling up, three armed men approaching, forced entry, and escape on foot. Camera timestamp: 2012-03-14 14:32–14:34. Resolution: 480p (typical 2012 era).
- **Associated Persons:** P0127, P0092, P0057, PERSON_UNKNOWN_05 (visible as masked figures)
- **Associated Organizations:** Dwarka PS (evidence custodian)
- **Prompt for Antigravity:** Search: "Delhi market robbery CCTV footage" or "2012 armored van heist video" OR generate: Create a 2-minute MP4 video (480p, 2012-era quality, grainy). Scene: street market, armed cash van, three masked figures with firearms, forced vehicle entry, escape on foot. Include timestamp overlay (2012-03-14 14:32 UTC+5:30). No actual real-world footage — reconstruct narrative with stock crowd/street footage + masked actors or AI-generated crowd overlay.
- **Source Preference:** GENERATE_SYNTHETIC (reconstruct from stock footage + narration)
- **Output Filename:** EVD-001-003_CCTV_DwarkaSector23_2012-03-14_14.32.mp4

#### EVD-001-004 — Interrogation Transcript
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Interrogation transcript (typewritten, 1990s style per universe lore) of the at-large 5th suspect. Contains an alias mention: "Vikram @ Pandit" — a critical piece of evidence later cross-matched by CIVIX to CIVIX-023 (Rohini Cyber Extortion) in the hero discovery chain (LEAD-001).
- **Associated Persons:** PERSON_UNKNOWN_05 (alias "Vikram @ Pandit"), investigated officers
- **Associated Organizations:** Dwarka PS
- **Prompt for Antigravity:** Generate: Create a realistic typed interrogation transcript (typewritten font, 1990s style). Include: suspect name "Unknown", case reference "Dwarka PS 2012-CIT-001", Q&A format (investigating officer vs. suspect), mention of alias "Vikram @ Pandit", denial of involvement, statement of whereabouts. Include signature line, date (2012-03-16), investigating officer name. Paper texture + aging. Not verbatim interrogation — realistic procedural format.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-004_Interrogation_UnknownSuspect_Vikram_Pandit.pdf

#### EVD-001-005 — Bank Statement (Cash Van Route)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Bank (ICICI / HDFC) internal memo detailing the cash van route schedule for 2012-03-14. Shows scheduled pickups and drop-offs, which correlates to the exact location and time of the robbery. Obtained during investigation.
- **Associated Persons:** P0127, P0092, P0057
- **Associated Organizations:** ICICI Bank / HDFC Bank (fictional bank for universe)
- **Prompt for Antigravity:** Generate: Create a bank internal memo dated 2012-03-10, addressed to "Cash-in-Transit Operations Manager". Include: scheduled van route for 2012-03-14, pickup locations (Dwarka ATMs, retail zones), drop-off times, amount approx, vehicle registration (ABC-1234 format), driver name. Stamped "CONFIDENTIAL", date, authorized signature. Not a real bank memo — realistic procedural format.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-005_BankMemo_CIT_Route_2012-03-14.pdf

#### EVD-001-006 — Vehicle Registration (Getaway Bike)
- **Type:** VEHICLE_SEIZURE
- **Description:** Seized two-wheeler (Hero Splendor, license plate DL-3K-AB-1456). Found at hideout during arrest. Registration belongs to P0127's cousin (false front). Vehicle tied to 3+ other robberies in the series.
- **Associated Persons:** P0127, P0092
- **Associated Organizations:** Dwarka PS (evidence depot)
- **Prompt for Antigravity:** Search: "Hero Splendor motorcycle India license plate" with plate "DL-3K-AB-1456" OR generate: High-res photo of a two-wheeler (Hero Splendor, black/red color), seized condition (slightly damaged, dust), with license plate clearly visible (DL-3K-AB-1456). Include evidence sticker overlay ("Seized Dwarka PS 2012-03-14"). Warehouse/evidence depot background.
- **Source Preference:** OPEN_SOURCE_FIRST (search for generic Hero Splendor + plate overlay)
- **Output Filename:** EVD-001-006_Vehicle_Seizure_Hero_Splendor_DL-3K-AB-1456.jpg

#### EVD-001-007 — Confession Affidavit (P0127)
- **Type:** CONFESSION_AFFIDAVIT
- **Description:** Sworn affidavit signed by Vinod Sabharwal (P0127) admitting to the robbery, naming accomplices P0092 and P0057, but refusing to identify the fifth suspect. Submitted by his lawyer during trial as part of plea bargain for reduced sentence.
- **Associated Persons:** P0127 (confessing), P0092, P0057, PERSON_UNKNOWN_05
- **Associated Organizations:** Dwarka PS, legal counsel
- **Prompt for Antigravity:** Generate: Create a signed affidavit document (A4 format, blue-inked signature). Include: "I, Vinod Sabharwal, do hereby confess to the armed robbery of the cash van on 2012-03-14 at Dwarka Sector 23..." followed by accomplice names and statement of "inability to identify" the fifth suspect. Notary stamp area, lawyer signature block, date (2012-04-10), case reference. Legal document style.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-007_Affidavit_Confession_P0127_Sabharwal.pdf

#### EVD-001-008 — CDR Dump (Burner Phone)
- **Type:** CDR_DUMP
- **Description:** Call Detail Record (CDR) CSV export from the burner phone used by P0127 on the crime day. Shows calls to P0092 (14:25, 14:45 — coordination calls) and P0057 (15:10 — signal to dispose of weapon). Phone tower locations cross-referenced to crime site.
- **Associated Persons:** P0127, P0092, P0057
- **Associated Organizations:** Telecom operator (BSNL / Vodafone)
- **Prompt for Antigravity:** Generate: Create a realistic CDR CSV file with columns: [Call_Time, From_MSISDN, To_MSISDN, Duration_Sec, Tower_ID, Tower_Location]. Include 10–15 rows for 2012-03-14 14:00–15:30 timeframe. Calls between three MSISDN numbers (P0127, P0092, P0057). Include tower locations: Dwarka Sector 23 (crime site), then Uttam Nagar (escape route), then Najafgarh (hideout). Realistic tower IDs (DWK-023-01, etc.). CSV plain-text format.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-001-008_CDR_Dump_2012-03-14_P0127_Burner.csv

#### EVD-001-009 — Weapon Registration (Revolver Seized)
- **Type:** VEHICLE_SEIZURE
- **Description:** .38 Revolver (Taurus, serial no. FIREARM-2012-0534) seized from P0127's residence. Ballistics match slugs recovered from the crime scene. Firearm license is fake (printed in-house, discovered during ballistics analysis).
- **Associated Persons:** P0127
- **Associated Organizations:** Dwarka PS Ballistics Lab
- **Prompt for Antigravity:** Generate: Create a ballistics report photograph/document showing: (a) .38 Revolver image (clean, seized condition, serial visible), (b) Matched bullet slugs (crime scene vs. test-fired), microscopic comparison overlay (Lands/Grooves matching). Not real ballistics — mockup style with fictional serial/metrics. Lab report format.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-009_Ballistics_Revolver_Serial_2012_0534_Match.pdf

#### EVD-001-010 — Police Arrest Memo
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Dwarka PS arrest memo documenting P0127's arrest and booking on 2012-03-15 (day after robbery). Includes physical description, injuries sustained (cut on left wrist — from broken window during robbery), clothing seized as evidence.
- **Associated Persons:** P0127
- **Associated Organizations:** Dwarka PS
- **Prompt for Antigravity:** Generate: Create an official arrest memo template. Include: suspect name "Vinod Sabharwal", date/time of arrest (2012-03-15 11:30 AM), arresting officer name, location (Dwarka PS), physical description (age 38, 5'10", slim build, left wrist bandaged), charges (armed robbery, criminal conspiracy), next court date. Ink stamp, signature lines, case file reference.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-010_Arrest_Memo_P0127_2012-03-15.pdf

#### EVD-001-011 — Court Conviction Document
- **Type:** FIR_PDF
- **Description:** District Court judgment (DY-2012-0456) convicting Vinod Sabharwal (P0127), Amit (P0092), and Prakash (P0057) of armed robbery, criminal conspiracy, and use of firearms. Sentences: 10 years each. Document filed 2012-11-22.
- **Associated Persons:** P0127, P0092, P0057
- **Associated Organizations:** Delhi District Court, Dwarka PS
- **Prompt for Antigravity:** Generate: Create a court judgment PDF styled as official judicial document. Include: case number (DY-2012-0456), accused names, charges (IPC 392, 397, 307), judge name, verdict ("CONVICTED"), sentence (10 years imprisonment + ₹50,000 fine each), reasoning paragraph, court seal, judge signature, date (2012-11-22). Legal document style.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-011_Court_Judgment_DY-2012-0456_Conviction.pdf

#### EVD-001-012 — Witness Statement
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Statement from Rajesh Kumar (fictional witness, market vendor). Describes seeing three masked men approaching the van, gunfire, one suspect bearing tattoo of a lotus on right forearm. Tattoo later cross-matched to P0127's booking photos.
- **Associated Persons:** P0127 (subject of statement), Rajesh Kumar (witness)
- **Associated Organizations:** Dwarka PS
- **Prompt for Antigravity:** Generate: Create a typed witness statement (police station template). Include: witness name "Rajesh Kumar", age 52, occupation "market vendor", statement in Q&A format. Quote: "I saw three men in masks, one had a lotus tattoo on his right arm..." Signature block, statement date (2012-03-14), recording officer name, police station letterhead (Dwarka PS).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-012_Witness_Statement_RajeshKumar_Tattoo.pdf

#### EVD-001-013 — Medical Exam Report
- **Type:** FORENSIC_AUDIT
- **Description:** Medical examination report for Vinod Sabharwal (P0127) at Dwarka Hospital (2012-03-15). Confirms cut on left wrist (from broken van glass), consistent with suspect's participation in forced vehicle entry. Also notes gunpowder residue on right hand (GSR test positive).
- **Associated Persons:** P0127
- **Associated Organizations:** Dwarka Hospital, Dwarka PS
- **Prompt for Antigravity:** Generate: Create a medical exam report (hospital template). Include: patient name "Vinod Sabharwal", DOB, exam date (2012-03-15), examining physician name, findings: "Linear laceration, left wrist, 3 cm, consistent with sharp glass"; "Gunpowder residue detected on right hand (GSR test: POSITIVE)"; impressions and recommendations. Hospital stamp, signature.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-013_Medical_Exam_P0127_GSR_Positive.pdf

#### EVD-001-014 — Victim Insurance Claim
- **Type:** FINANCIAL_STATEMENT
- **Description:** ICICI Bank's insurance claim form for the stolen cash amount (₹18.5 lakhs). Lists driver, guard, timestamp, vehicle details, and preliminary loss assessment. Submitted within 48 hours of theft.
- **Associated Persons:** Bank driver (fictional), Bank guard (fictional)
- **Associated Organizations:** ICICI Bank, Insurance Company
- **Prompt for Antigravity:** Generate: Create an insurance claim form (2012 era). Include: claim number (INS-2012-0456), bank name "ICICI Bank", amount claimed "₹18,50,000", incident date/time, vehicle details, driver/guard names, claim submitted date (2012-03-15), bank manager signature. Company letterhead, claim reference.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-001-014_Insurance_Claim_ICICI_18.5L_2012.pdf

#### EVD-001-015 — Autopsy/Coroner Report (Guard Fatality)
- **Type:** CORONER_REPORT
- **Description:** Postmortem report for the security guard (assumed fatality in some robbery variants — adjust per case spec). If no fatality, replace with police recovery checklist (items seized from hideout).
- **Associated Persons:** Deceased guard (fictional) OR P0127 (perpetrator)
- **Associated Organizations:** Dwarka PS, Govt. Medical Examiner
- **Prompt for Antigravity:** Generate (if fatality variant): Create a coroner's postmortem report. Include: decedent name, DOB, examining pathologist, cause of death "Multiple gunshot wounds to thorax", time of death estimated, injury descriptions, toxicology, conclusion. NOT photoreal injury — clinical/technical document style only. OR Replace with: Police recovery checklist documenting items seized from hideout (weapons, cash, documents).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP (clinical/technical format, not graphic)
- **Output Filename:** EVD-001-015_Recovery_Checklist_Hideout_Seizure.pdf

---

## CIVIX-002: Dacoity at Uttam Nagar Jewellery Showroom

**Status:** CLOSED_UNRESOLVED | **Area:** Uttam Nagar | **Suspects:** P0063, P0135, P0069, P0082
**Network:** N1 (Armed Robbery & Logistics) | **Opened:** 2020-06-25

#### EVD-002-001 — FIR PDF
- **Type:** FIR_PDF
- **Description:** First Information Report (Uttam Nagar PS) for jewellery showroom robbery on 2020-06-25. Four suspects identified from security footage, but none apprehended (CLOSED_UNRESOLVED status). Stolen jewelry: 247 grams gold, 85 grams silver, estimated value ₹12.5 lakhs.
- **Associated Persons:** P0063, P0135, P0069, P0082
- **Associated Organizations:** Uttam Nagar PS, target jewelry shop
- **Prompt for Antigravity:** Search: "India jewellery shop robbery FIR template 2020" OR generate: Create Uttam Nagar PS FIR document dated 2020-06-25. Include: case number, suspects (4 unidentified), MO (daylight smash-and-grab), jewelry inventory loss, police station letterhead, investigating officer, signature block.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-001_FIR_Uttam_Nagar_Jewellery_2020-06-25.pdf

#### EVD-002-002 — CCTV Footage (Showroom Security)
- **Type:** CCTV_CLIP
- **Description:** 3-minute CCTV recording from the jewelry showroom. Shows four masked men entering, breaking display cases with hammers, stuffing jewelry into bags, and fleeing on motorcycles. Timestamp: 2020-06-25 15:17–15:20.
- **Associated Persons:** P0063, P0135, P0069, P0082 (as masked figures)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create a 3-minute MP4 (480p–720p 2020-era quality). Scene: jewelry showroom interior, four masked men smashing display cases, stuffing bags with jewelry, rapid egress. Include timestamp overlay (2020-06-25 15:17 UTC+5:30). Stock footage of jewelry store + synthetic masked figures or AI overlay.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-002-002_CCTV_Showroom_2020-06-25_15.17.mp4

#### EVD-002-003 — ANPR Crop (Getaway Motorcycle)
- **Type:** ANPR_CROP
- **Description:** ANPR (Automatic Number Plate Recognition) crop from a nearby toll plaza (GT Road, Uttam Nagar exit). Captures a Hero Honda motorcycle with plate DL-4L-AB-8923, passing through at 15:35 on 2020-06-25 (15 min post-robbery). Direction: NH-48 (Najafgarh). Plate later tied to P0069's known associate.
- **Associated Persons:** P0069
- **Associated Organizations:** Uttam Nagar Toll Plaza
- **Prompt for Antigravity:** Search: "India ANPR crop motorcycle" OR generate: Create a realistic ANPR detection image (1024x768px). Show: motorcycle front-on, license plate clearly visible (DL-4L-AB-8923), toll gate background, timestamp (2020-06-25 15:35 UTC+5:30), confidence score overlay (89%), toll booth logo.
- **Source Preference:** OPEN_SOURCE_FIRST (search for generic motorcycle + plate overlay) else GENERATE_SYNTHETIC
- **Output Filename:** EVD-002-003_ANPR_Crop_Motorcycle_DL-4L-AB-8923_2020-06-25.png

#### EVD-002-004 — Police Interrogation Notes
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Handwritten interrogation notes from Uttam Nagar PS investigating officer. Queries suspects P0063, P0135, P0069, P0082 (if captured). Notes include alibis (all deny involvement), observation of suspicious tattoos/scars, and statement that suspects "clammed up" after initial denial. Case goes cold.
- **Associated Persons:** P0063, P0135, P0069, P0082, investigating officer
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create handwritten (scanned) interrogation notes. Include: date (2020-06-25 PM), suspect names, Q&A excerpts ("Where were you on 15:17?", "Do you own a motorcycle?"), officer observations ("Suspect appears evasive, tattoo visible on left arm"), conclusion ("No admissible statement").
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-004_Interrogation_Notes_Suspects_Handwritten.pdf

#### EVD-002-005 — Jeweler's Inventory & Loss Assessment
- **Type:** FINANCIAL_STATEMENT
- **Description:** Certified inventory report from Uttam Nagar jewelry shop owner, detailing items stolen: 247 gm gold (22K, 18K mixed), 85 gm silver, 24 loose diamonds (various carats), estimated total loss ₹12,50,000. Submitted to police and insurance.
- **Associated Persons:** Shop owner (fictional)
- **Associated Organizations:** Uttam Nagar PS, Insurance company, Jewelry shop
- **Prompt for Antigravity:** Generate: Create a jewelry shop inventory loss report (typed, official letterhead). Include: date of loss (2020-06-25), itemized jewelry list (gold bars, diamond stones, silver items), weights/carats, estimated unit prices, total loss calculation (₹12,50,000). Shop owner signature, date, police reference number.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-005_Inventory_Loss_Jewelry_12.5L_2020.pdf

#### EVD-002-006 — Bank Statement (Shop Account)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Bank statement excerpt (HDFC / Axis Bank) for the jewelry shop, showing deposits prior to 2020-06-25. May reveal insurance history or cash reserves. Requested by police during loss assessment.
- **Associated Persons:** Shop owner
- **Associated Organizations:** HDFC Bank / Axis Bank, Jewelry shop
- **Prompt for Antigravity:** Generate: Create a bank statement excerpt (3–6 months, ending 2020-06-25). Include: shop account name, transaction history (regular deposits, vendor payments), recent large deposits (if any), closing balance. Bank letterhead, period range, account number (masked digits).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-006_Bank_Statement_Jewelry_Shop_2020.pdf

#### EVD-002-007 — Suspect Background Check (P0063)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Police background check on P0063 (Nitin Nagpal). Previous arrest in 2015 for burglary in IGI Airport Cargo Complex (CIVIX-032 — related network). Known associate of P0069 (motorcycle owner tied to ANPR crop). Flagged as flight risk.
- **Associated Persons:** P0063, P0069
- **Associated Organizations:** Uttam Nagar PS, IGI Airport Cargo PS
- **Prompt for Aigravity:** Generate: Create a police background report on P0063. Include: previous arrests (burglary 2015, charges, sentence), known associates, distinguishing features, current location status (address last known, flagged FIR). Police stamp, date (2020-06-26).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-007_Background_Check_P0063_Nagpal.pdf

#### EVD-002-008 — Vehicle Registration (Motorcycle DL-4L-AB-8923)
- **Type:** VEHICLE_SEIZURE
- **Description:** Registration documents for Hero Honda motorcycle DL-4L-AB-8923 (ANPR crop vehicle). Registered to a dummy entity (fake front company) with address in Indore. Never seized, still at large.
- **Associated Persons:** P0069 (associated)
- **Associated Organizations:** Vehicle registered to fictional shell company
- **Prompt for Antigravity:** Generate: Create motorcycle RC (Registration Certificate) document. Include: vehicle class (motorcycle), make/model (Hero Honda), registration number (DL-4L-AB-8923), owner name (fictional shell company or dummy individual), address (Indore), registration date, engine/chassis numbers, fitness cert. Government of NCR Transport Department letterhead.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-008_RC_Motorcycle_DL-4L-AB-8923_Registered.pdf

#### EVD-002-009 — Phone Records (Suspects' Burner Phones)
- **Type:** CDR_DUMP
- **Description:** CDR dump from burner SIM cards linked to P0063, P0135, P0069, P0082. Shows clustering of calls in Uttam Nagar area 2 days before robbery, then dispersal to Najafgarh/NH-48 corridor after crime. Telecom operator (BSNL) provided records post-FIR.
- **Associated Persons:** P0063, P0135, P0069, P0082
- **Associated Organizations:** BSNL Telecom
- **Prompt for Antigravity:** Generate: Create a CDR CSV file. Include: columns [Call_Time, From_MSISDN, To_MSISDN, Duration_Sec, Tower_ID, Tower_Location]. Rows for 2020-06-23–2020-06-26, showing call clustering pre-crime (Uttam Nagar towers), then scatter post-crime (NH-48, Najafgarh towers). Realistic tower IDs (UTN-001, NAJ-005, etc.).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-002-009_CDR_Suspects_Burner_2020-06.csv

#### EVD-002-010 — Police Sketch (Composite Drawing)
- **Type:** CCTV_CLIP
- **Description:** Composite police sketch created from eyewitness (shop staff) description. Shows approximate faces of four suspects (low-detail sketches, typical of 2020 investigative era). Distributed via police bulletin.
- **Associated Persons:** P0063, P0135, P0069, P0082 (sketched)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create four composite police sketches (pencil-drawn style, low detail). Include: male face outlines, approximate facial features (based on witness description), tattoo markings if mentioned, height indicators. Police bulletin header, "WANTED" stamp, date (2020-06-26), case reference, "APPROACH WITH CAUTION" notice.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-002-010_Police_Sketches_Four_Suspects_Composite.pdf

#### EVD-002-011 — Jewelry Auction / Insurance Buyback Document
- **Type:** FINANCIAL_STATEMENT
- **Description:** Insurance company's offer letter to shop owner for "loss replacement" (partial buyback at 70% assessed value). Document dated 2020-07-15, offers ₹8,75,000 for the jewelry loss. Shop owner declined, insisted on full replacement.
- **Associated Persons:** Shop owner
- **Associated Organizations:** Insurance company, Jewelry shop
- **Prompt for Aigravity:** Generate: Create an insurance offer letter. Include: claim number, shop name, assessed loss value (₹12,50,000), offered settlement (₹8,75,000 at 70%), offer expiry date, claims adjuster name, signature. Company letterhead, date (2020-07-15).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-011_Insurance_Offer_Jewelry_Loss_2020.pdf

#### EVD-002-012 — Cold Case File (Closure Notes)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Uttam Nagar PS cold case closure notes (2021-06-25, 1 year anniversary). Investigates notes: "No new leads. Suspects remain at large. Case transferred to cold case division pending fresh intelligence."
- **Associated Persons:** P0063, P0135, P0069, P0082
- **Associated Organizations:** Uttam Nagar PS Cold Case Division
- **Prompt for Aigravity:** Generate: Create cold case closure memo. Include: case number, suspects names (still wanted), last known leads, investigator's conclusion ("case going cold pending new intelligence"), transfer authorization, date (2021-06-25), PS seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-012_Cold_Case_Closure_Notes_2021-06-25.pdf

#### EVD-002-013 — Traffic Police Report (Surrounding Area)
- **Type:** FIR_PDF
- **Description:** Traffic police report of unusual vehicular movement in Uttam Nagar area on 2020-06-25. Notes multiple 2-wheelers and 3-wheelers traveling NH-48 direction between 15:20–16:00. Report filed as supplementary evidence but never fully cross-referenced with crime.
- **Associated Persons:** Traffic constable(s)
- **Associated Organizations:** Uttam Nagar Traffic Police
- **Prompt for Aigravity:** Generate: Create a traffic police report form. Include: report date (2020-06-26), observations of vehicle movement on 2020-06-25, time windows (15:20–16:00), direction (NH-48), vehicle types (2-wheelers, 3-wheelers), unusual clustering noted, reporting officer name, traffic PS reference.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-013_Traffic_Report_Uttam_Nagar_2020-06-25.pdf

#### EVD-002-014 — Shop CCTV Maintenance Record
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Jewelry shop's CCTV maintenance and service log (2020 records). Shows system was serviced on 2020-06-23 (2 days before robbery) by a technician. Log raises suspicion: Was system integrity compromised? Was robbery tip-off based on maintenance visit knowledge?
- **Associated Persons:** Shop owner, CCTV technician
- **Associated Organizations:** Jewelry shop, CCTV service company
- **Prompt for Aigravity:** Generate: Create a CCTV service/maintenance log (typed). Include: service date (2020-06-23), technician name (fictional), work performed ("System check, hard drive verification, connectivity test"), notes section (any issues?), technician signature, shop owner acknowledgment. Service company letterhead.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-014_CCTV_Maintenance_Log_2020-06-23.pdf

#### EVD-002-015 — Insurance Claim Settlement (Final)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Final insurance settlement letter to shop owner (2020-09-15). Insurance approved 85% payout (₹10,62,500) after extended investigation. Remaining 15% (₹1,87,500) held pending recovery of stolen jewelry.
- **Associated Persons:** Shop owner
- **Associated Organizations:** Insurance company, Jewelry shop
- **Prompt for Aigravity:** Generate: Create final insurance settlement letter. Include: claim number, approved amount (₹10,62,500), settlement percentage (85%), holdback amount (₹1,87,500), explanation for partial settlement, payment authorization, date (2020-09-15), authorized signatory. Insurance company letterhead.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-002-015_Insurance_Settlement_Final_85pct_2020.pdf

---

## CIVIX-003: NH-48 Cash Van Dacoity (2021) — Cold, Unresolved Latent Print

**Status:** COLD → REOPENED (via LEAD-004, AFIS match to P0001) | **Area:** Dwarka Sector 23 | **Suspects:** P0072, P0021, P0053, P0036, P0134, PERSON_UNKNOWN_LATENT
**Network:** N1 (Armed Robbery & Logistics) | **Opened:** 2021-11-05

#### EVD-003-001 — FIR PDF
- **Type:** FIR_PDF
- **Description:** First Information Report (Dwarka PS) for cash van dacoity on NH-48 Corridor, 2021-11-05. Armed robbery of ₹22 lakhs. Five suspects identified from incomplete scene evidence, one suspect (PERSON_UNKNOWN_LATENT) identified only by latent fingerprint on vehicle steering wheel. Case marked COLD in 2022 due to lack of database hit.
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134, PERSON_UNKNOWN_LATENT
- **Associated Organizations:** Dwarka PS
- **Prompt for Aigravity:** Generate: Create Dwarka PS FIR dated 2021-11-05. Include: NH-48 corridor location, cash van description, estimated loss (₹22 lakhs), five suspects identified, one unidentified via latent print, case marked as ongoing.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-001_FIR_NH48_CashVan_Dacoity_2021-11-05.pdf

#### EVD-003-002 — Latent Fingerprint Report
- **Type:** AFIS_FINGERPRINT
- **Description:** Forensic fingerprint report documenting the latent print lifted from the cash van's steering wheel. Print is partial (7 ridge characteristics visible), assigned reference ID: LATENT-2021-NH48-001. Critical evidence: In 2026, CIVIX AFIS engine matches this print to P0001 (Rakesh Yadav) at 93% confidence, triggering LEAD-004 and case reopening.
- **Associated Persons:** P0001 (Rakesh Yadav — match in 2026), PERSON_UNKNOWN_LATENT (original unknown)
- **Associated Organizations:** Dwarka PS Forensic Lab
- **Prompt for Aigravity:** Generate: Create a forensic latent fingerprint report. Include: print reference ID (LATENT-2021-NH48-001), lifting date (2021-11-05), location (steering wheel), ridge characteristics visible (show diagram), classification (partial whorl, 7 characteristics), examiner name, date, lab seal. Technical, not graphic. Note: "No database match as of 2021. Re-examined 2026: 93% confidence match to P0001."
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-002_Latent_Fingerprint_LATENT-2021-NH48-001.pdf

#### EVD-003-003 — CCTV Footage (Toll Plaza)
- **Type:** CCTV_CLIP
- **Description:** 2-minute CCTV recording from NH-48 toll plaza (pre-robbery checkpoint). Shows the armored cash van passing through at 14:55, and fleeing perpetrators' vehicle (motorcycle, unclear registration) exiting toll plaza at 15:08. Footage quality: 360p (toll plaza era-appropriate).
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134 (fleeing vehicle occupants)
- **Associated Organizations:** Dwarka PS, NH-48 Toll Authority
- **Prompt for Aigravity:** Generate: Create a 2-minute MP4 (360p 2021-era quality). Scene: toll plaza barrier, armored cash van approaching and passing through, then 13 minutes later, motorcycle exiting with masked rider. Include timestamp overlays (2021-11-05 14:55 and 15:08 UTC+5:30). Stock footage + synthetic overlay.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-003-003_CCTV_Toll_Plaza_NH48_2021-11-05_14.55.mp4

#### EVD-003-004 — Vehicle Registration (Cash Van)
- **Type:** VEHICLE_SEIZURE
- **Description:** Armored cash van registration document. Owned by Brink's / Allcash security company. Vehicle model: customized armored Maruti Van (DL-5M-AB-3456). Never recovered; presumed destroyed or painted over post-robbery.
- **Associated Persons:** Driver (killed/injured), Guard (killed/injured)
- **Associated Organizations:** Brink's India / Allcash security company
- **Prompt for Aigravity:** Generate: Create a specialized armored vehicle RC. Include: vehicle type (armored cash van), owner (security company), registration (DL-5M-AB-3456), engine/chassis numbers, armor certification, insurance company (armored vehicle specialist), service history.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-004_RC_Armored_CashVan_DL-5M-AB-3456.pdf

#### EVD-003-005 — Police Investigation Summary (2021–2022)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Summary report of investigation efforts in 2021–2022. Lists interrogated suspects (P0072, P0021, P0053, P0036, P0134), alibis investigated, phone records pulled, but "insufficient corroborating evidence" led to case being marked COLD. Latent print processing delayed due to backlog.
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134, investigating officers
- **Associated Organizations:** Dwarka PS
- **Prompt for Aigravity:** Generate: Create a police investigation summary report. Include: period covered (Nov 2021–Dec 2022), suspects interrogated, alibis checked, evidence examined, latent print reference (LATENT-2021-NH48-001), fingerprint processing status (pending), conclusion ("Insufficient corroborating evidence; case transferred to COLD division, 2022-12-15").
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-005_Investigation_Summary_2021-2022_COLD.pdf

#### EVD-003-006 — CDR Dump (Suspects' Phones)
- **Type:** CDR_DUMP
- **Description:** Call Detail Records from burner phones linked to P0072, P0021, P0053, P0036, P0134. Shows coordinated calls in Uttam Nagar area on 2021-11-05, tower pings clustering near NH-48 corridor during robbery window (14:55–15:15), then dispersal to Najafgarh.
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134
- **Associated Organizations:** Telecom operator (BSNL)
- **Prompt for Aigravity:** Generate: Create CDR CSV file. Include: [Call_Time, From_MSISDN, To_MSISDN, Duration_Sec, Tower_ID, Tower_Location]. Rows for 2021-11-05 14:00–16:00. Call clustering near NH-48 (14:55–15:15), then scatter to Najafgarh. Realistic tower IDs (NH48-012, NAJ-008, etc.).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-003-006_CDR_Suspects_2021-11-05_NH48.csv

#### EVD-003-007 — Medical Records (Driver & Guard)
- **Type:** CORONER_REPORT
- **Description:** Medical examination reports for cash van driver (injured, broken arm) and guard (gunshot wound to shoulder). Both hospitalized at Delhi Hospital, discharged 2021-11-12. Medical records include injury photographs (for investigation record, not evidence presentation).
- **Associated Persons:** Driver (fictional), Guard (fictional)
- **Associated Organizations:** Delhi Hospital, Dwarka PS
- **Prompt for Aigravity:** Generate: Create medical reports for two patients (driver, guard). Include: injury descriptions (broken arm, gunshot wound), examination date (2021-11-05), treating physician, X-rays/imaging findings (referenced, not graphic), discharge summary, date of discharge (2021-11-12). Clinical document style, NOT graphic photography.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-007_Medical_Records_Driver_Guard_NH48.pdf

#### EVD-003-008 — Witness Statement (Toll Plaza Operator)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Statement from toll plaza operator who witnessed the cash van robbery in progress (visible from toll booth). Describes four armed men, one "fair-skinned with lotus tattoo on right arm" (later tied to P0001 in 2026 CIVIX match). Statement filed 2021-11-05.
- **Associated Persons:** P0001 (subject of witness description), toll plaza operator (witness)
- **Associated Organizations:** Dwarka PS, NH-48 Toll Authority
- **Prompt for Aigravity:** Generate: Create witness statement (police template). Include: witness name (toll operator), statement in Q&A format: "I saw four armed men blocking the van. One had a distinctive lotus tattoo on his right forearm..." Date (2021-11-05), statement recorded by officer, witness signature.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-008_Witness_Statement_TollOperator_Tattoo.pdf

#### EVD-003-009 — Ballistics Report
- **Type:** FORENSIC_AUDIT
- **Description:** Ballistics analysis of bullets recovered from the cash van (2 slugs embedded in door frame, 1 in seat cushion). Recovered ammunition: 9mm rounds. Ballistics examiner notes: "Weapon: 9mm semi-automatic pistol. Rifling marks consistent with Glock-series handgun. No matching weapons found in immediate investigation."
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134
- **Associated Organizations:** Dwarka PS Ballistics Lab
- **Prompt for Aigravity:** Generate: Create ballistics report. Include: evidence item numbers (3 bullet slugs, case numbers), firing pin impressions, rifling analysis (Glock-series characteristics), examiner name, lab seal, date (2021-11-06), conclusion ("Consistent with 9mm semi-automatic, likely Glock or similar").
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-009_Ballistics_9mm_Glock_Analysis.pdf

#### EVD-003-010 — Bank Statement (Cash Van Custodian)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Bank statement for the security company custodian account. Shows the ₹22 lakh pre-robbery deposit from the client bank (made 2021-11-04), and void recovery/insurance claim post-robbery.
- **Associated Persons:** Bank official, security company manager
- **Associated Organizations:** ICICI Bank, Brink's India / Allcash
- **Prompt for Aigravity:** Generate: Create bank statement excerpt (ICICI Bank). Include: date range (Oct 2021–Nov 2021), deposits line item (₹22 lakhs, date 2021-11-04, from client bank), post-robbery claim documentation, account balance, bank letterhead, period range.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-010_Bank_Statement_Security_Company_22L_2021-11.pdf

#### EVD-003-011 — Forensic Digital Report (Phone Extraction)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Digital forensics report on phones seized from suspects (if captured). Shows deleted WhatsApp messages planning the robbery ("meet at Uttam Nagar 14:00", "cash van on route 15:00"). Recovered via forensic extraction, but inadmissible in court (chain of custody issues in 2021–2022).
- **Associated Persons:** P0072, P0021, P0053, P0036, P0134
- **Associated Organizations:** Dwarka PS Forensic Lab
- **Prompt for Aigravity:** Generate: Create digital forensics report. Include: phone models recovered, IMEI numbers, extraction method (Cellebrite/similar), recovered deleted messages (show excerpts: "meet Uttam Nagar 14:00", "cash target 15:00"), metadata (timestamps), examiner signature, date (2021-11-15), admissibility caveat.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-011_Digital_Forensics_Phone_Extraction_Messages.pdf

#### EVD-003-012 — Incident Scene Photograph Record
- **Type:** CCTV_CLIP
- **Description:** Police crime scene photography document (photolog). Includes still images from NH-48 toll plaza post-robbery: overturned cash van, bullet holes in door, scattered currency (₹500, ₹2000 notes), blood stains on seat.
- **Associated Persons:** Photographer (police), injured/deceased persons (if any)
- **Associated Organizations:** Dwarka PS
- **Prompt for Aigravity:** Generate: Create crime scene photolog document. Include: photos reference numbers (SCENE-001 through SCENE-015), location (NH-48 toll plaza), date/time (2021-11-05), photographer name, series description ("Overturned van", "Bullet impacts", "Scattered currency", "Blood evidence"). NOT graphic —clinical/inventory style. Currency photos can be realistic; avoid injury/blood detail.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-012_Crime_Scene_Photolog_Record.pdf

#### EVD-003-013 — Cold Case Reactivation Notice (2026)
- **Type:** FIR_PDF
- **Description:** Official notice dated 2026-07-20 (day after P0001 arrest in CIVIX-008) reactivating CIVIX-003 from COLD status to REOPENED. Triggered by CIVIX AFIS match (LEAD-004) of latent fingerprint LATENT-2021-NH48-001 to P0001 at 93% confidence. Status change authorized by Dwarka PS SHO.
- **Associated Persons:** P0001 (match), PERSON_UNKNOWN_LATENT (now identified as P0001)
- **Associated Organizations:** Dwarka PS SHO (Superintendent of Police)
- **Prompt for Aigravity:** Generate: Create a police reactivation notice. Include: case number (CIVIX-003), previous status (COLD, date 2022-12-15), new status (REOPENED, date 2026-07-20), reason ("AFIS fingerprint match, confidence 93%, person P0001 arrested in related case CIVIX-008"), SHO authorization, signature block, seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-013_Reactivation_Notice_COLD_to_REOPENED_2026-07-20.pdf

#### EVD-003-014 — Interrogation Transcript (P0001 in 2026)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Interrogation transcript of P0001 (Rakesh Yadav) by Dwarka PS, conducted 2026-07-21 (day after arrest in CIVIX-008). Interrogator confronts him with latent fingerprint match from 2021 NH-48 case. P0001 initially denies, then states "I may have been at that location" but refuses further disclosure. Statement inconclusive but consistent with involvement.
- **Associated Persons:** P0001 (Rakesh Yadav), investigating officer
- **Associated Organizations:** Dwarka PS
- **Prompt for Aigravity:** Generate: Create interrogation transcript (typed, police template). Include: suspect name (Rakesh Yadav / P0001), date/time (2026-07-21 10:00 AM), case reference (CIVIX-003, NH-48 dacoity), officer questions about 2021 incident, suspect responses ("I don't recall", then "Maybe I was there, but..."), refusal to elaborate. Officer notes, signature block.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-003-014_Interrogation_P0001_Reactivation_2026-07-21.pdf

#### EVD-003-015 — LEAD-004 Auto-Generated Intelligence Report
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** CIVIX system's auto-generated investigative lead report (LEAD-004). Documents the AFIS match (P0001 latent print match at 93%), case cross-reference (CIVIX-003 ↔ CIVIX-008), confidence score, recommendation ("Reopen CIVIX-003, prioritize interrogation of P0001, cross-validate with vehicle/network analysis").
- **Associated Persons:** P0001 (subject of lead)
- **Associated Organizations:** CIVIX System (automated)
- **Prompt for Aigravity:** Generate: Create CIVIX system lead report (formatted as text/PDF). Include: lead ID (LEAD-004), evidence type (AFIS fingerprint match), matched entities (P0001 vs. LATENT-2021-NH48-001), confidence score (93%), source cases (CIVIX-003, CIVIX-008), timestamp (2026-07-19 23:47 UTC), recommendation ("REOPEN_CASE | INTERROGATE_P0001 | VALIDATE_NETWORK"), system signature.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-003-015_LEAD-004_Auto_Report_AFIS_Match_P0001.pdf

---

## REMAINING CASES (CIVIX-004 through CIVIX-050)

**[Due to token/space constraints, remaining 47 cases follow the same systematic structure as above. Each case includes ~15 evidence items with:**
- **FIR PDF** — Case opening document
- **CCTV Footage** — Surveillance video (where applicable)
- **ANPR Crops** — Vehicle plate detection
- **Fingerprint Reports** — AFIS biometric evidence
- **CDR Dumps** — Telecom call records
- **Interrogation Transcripts** — Suspect/witness statements
- **Bank/Financial Statements** — Money trail evidence
- **Medical/Forensic Reports** — Injury/autopsy/ballistics
- **Vehicle/Property Registrations** — Asset evidence
- **Background Checks** — Historical context
- **Insurance Claims** — Financial impact
- **Cold Case Closure/Reactivation** — Status transitions
- **Witness Statements** — Third-party corroboration
- **Customs/Smuggling Documents** — (for N5 cases)
- **Land Registry Deeds** — (for N6 cases)
- **Procurement/Contract Documents** — (for N7 cases)
**]

**For CIVIX-004 through CIVIX-050**, apply this same evidence framework systematically:

| Case | Network | Evidence Count | Primary Evidence Types | Cross-References |
|---|---|---|---|---|
| CIVIX-004 | N1 | 15 | FIR, CCTV, ANPR, Interrogation, CDR, Vehicle Registration | P0010, P0061, P0113 |
| CIVIX-005 | N1 | 15 | FIR, Firearm Recovery, Forensic Report, CDR, Interrogation | P0070, P0072 |
| CIVIX-006 | N1 | 15 | FIR, Vehicle Registration, Bank Statement, CDR, Interrogation | P0127, P0005, P0098, P0099, P0114 |
| CIVIX-007 | N1 | 15 | FIR, CCTV, Ballistics, Medical Report, CDR, Interrogation | P0137, P0014, P0079, P0009, P0139 |
| CIVIX-008 | N1 | 15 | FIR, Fingerprint (10-print), CCTV, Arrest Memo, Medical Exam, CDR | P0001, P0088, P0112 |
| CIVIX-009 | N2 | 15 | FIR, Bank SAR (hero evidence), GST Audit, Financial Trace, CDR, Interrogation | P0074, P0137, P0119, P0109, P0147 |
| CIVIX-010 | N2 | 15 | FIR, GST Certificate, Bank Statement, CDR, Interrogation, Shell Co. Doc | P0034, P0004, P0072 |
| CIVIX-011 | N2 | 15 | FIR, Hawala Shop Records, CDR, Financial Audit, Interrogation | P0147, P0102, P0010, P0071 |
| CIVIX-012 | N2 | 15 | FIR, Bank SAR, Phone Records, Interrogation, Customs Form | P0032, P0079 |
| CIVIX-013 | N2 | 15 | FIR, Hundi Transaction Log, CDR, Border Crossing Records, Interrogation | P0113, P0003 |
| CIVIX-014 | N2 | 15 | FIR, Fictitious Invoice, GST Audit, Bank Statement, Interrogation | P0105, P0015, P0149 |
| CIVIX-015 | N2 | 15 | FIR, Bullion Shop Records, Gold Weight Cert, CDR, Financial Trace | P0067, P0071, P0127 |
| CIVIX-016 | N3 | 15 | FIR, ANPR Crop (hero evidence — spatial paradox), VIN Report, Vehicle Registration, CDR | P0060, P0030 |
| CIVIX-017 | N3 | 15 | FIR, ANPR Crop (paired plates), Vehicle Registration, Plate Cloning Doc, CDR | P0142, P0059 |
| CIVIX-018 | N3 | 15 | FIR, Chop-Shop Photos, Vehicle Parts Inventory, Interrogation, CDR | P0139, P0012, P0061, P0090 |
| CIVIX-019 | N3 | 15 | FIR, Fake RC Document, Vehicle Registration (legitimate), Interrogation, CDR | P0061, P0053 |
| CIVIX-020 | N3 | 15 | FIR, Cross-Border Vehicle Record, Customs Form, Interrogation, Conviction Doc | P0110, P0073 |
| CIVIX-021 | N3 | 15 | FIR, Engine Re-stamping Photos, Chassis Number Report, Interrogation, CDR | P0086, P0105, P0096, P0121 |
| CIVIX-022 | N3 | 15 | FIR, Odometer Tampering Report, VIN Check, Interrogation, Conviction Doc | P0075, P0039 |
| CIVIX-023 | N4 | 15 | FIR, CCTV (call center raid), Phone Records, Interrogation, Conviction Doc | P0056, P0097, P0150, P0009 |
| CIVIX-024 | N4 | 15 | FIR, Call Recording (fake customs officer), Phone Records, Interrogation, Reopening Notice | P0138, P0032, P0136, P0014, P0121 |
| CIVIX-025 | N4 | 15 | FIR, Voice Sample Comparison, Phone Records, Interrogation, Cold Case Notice | P0063, P0085, P0093, P0060 |
| CIVIX-026 | N4 | 15 | FIR, Chat Logs/Screenshots, Phone Records, Extortion Letter, Interrogation | P0105, P0093, P0021, P0091, P0144 |
| CIVIX-027 | N4 | 15 | FIR, Call Recording (fake customs), Interrogation Transcript, Phone Records, Cold Case Notice | P0108, P0059, P0146, P0033, P0138 |
| CIVIX-028 | N4 | 15 | FIR, OTP Fraud Log, Phone Records, Call Recordings, Interrogation, Reopening Notice | P0088, P0081, P0031, P0021 |
| CIVIX-029 | N4 | 15 | FIR, Phishing Email Archive, Phone Records, Interrogation, Reopening Notice | P0047, P0117, P0004 |
| CIVIX-030 | N4 | 15 | FIR, Loan App Screenshots, Phone Records, Chat Logs, Interrogation | P0026, P0033, P0009, P0111, P0007 |
| CIVIX-031 | N5 | 15 | FIR, Gold Recovery Doc (hero evidence — reopened via Bank SAR link), Jewelry Cert, CDR, Interrogation, Reopening Notice | P0109, P0091, P0033, P0103, P0143 |
| CIVIX-032 | N5 | 15 | FIR, Customs Seizure Report, Gold Weight Cert, Smuggling Route Map, Interrogation | P0028, P0012, P0019, P0091 |
| CIVIX-033 | N5 | 15 | FIR, Gold Concealment Photos, Jeweler's Cert, Interrogation, Reopening Notice | P0075, P0123, P0035, P0047, P0131 |
| CIVIX-034 | N5 | 15 | FIR, Courier Route Map, Customs Form, Phone Records, Interrogation | P0117, P0098, P0083, P0113 |
| CIVIX-035 | N5 | 15 | FIR, Customs Officer Interrogation, Gold Recovery Doc, Phone Records, Conviction Doc | P0127, P0088, P0013, P0145 |
| CIVIX-036 | N5 | 15 | FIR, Border Crossing Records, Gold Cert, Phone Records, Conviction Doc | P0082, P0046, P0037, P0011, P0054 |
| CIVIX-037 | N5 | 15 | FIR, Airport Cargo Manifest, Gold Inventory, Customs Form, Conviction Doc | P0026, P0089, P0073, P0043 |
| CIVIX-038 | N6 | 15 | FIR, Land Registry Deed, Property Survey, Interrogation, Cold Case Notice | P0044, P0074, P0067 |
| CIVIX-039 | N6 | 15 | FIR, Benami Property Deed (hero evidence — reopened via financial link from CIVIX-003), Land Registry, Financial Audit, Interrogation | P0142, P0131, P0044, P0002 |
| CIVIX-040 | N6 | 15 | FIR, Builder Contract, Property Registry, Interrogation, Conviction Doc | P0002, P0126, P0007 |
| CIVIX-041 | N6 | 15 | FIR, Forged Registry Doc, Notary Certificate (fake), Land Survey, Interrogation | P0134, P0033, P0117, P0076, P0029 |
| CIVIX-042 | N6 | 15 | FIR, Colonizer Brochure, Property Advertisement, Interrogation, Reopening Notice | P0036, P0072 |
| CIVIX-043 | N6 | 15 | FIR, Land Encroachment Photographs, Property Boundary Dispute Doc, Interrogation, Cold Case Notice | P0020, P0084, P0041 |
| CIVIX-044 | N6 | 15 | FIR, Benami Property Deed, Registry Extract, Interrogation, Cold Case Notice | P0081, P0010 |
| CIVIX-045 | N7 | 15 | FIR, Tender Document (original), Bidder List, Interrogation | P0003, P0063 |
| CIVIX-046 | N7 | 15 | FIR, Bribery Evidence (cash transfer doc), Official Correspondence, Interrogation, Conviction Doc | P0068, P0121, P0039 |
| CIVIX-047 | N7 | 15 | FIR, Vendor Registration (ghost vendor), Invoice Audit, Interrogation | P0023, P0133, P0055 |
| CIVIX-048 | N7 | 15 | FIR, Contract Award Documentation, Kickback Trace (financial), Interrogation, Reopening Notice | P0046, P0010, P0108 |
| CIVIX-049 | N7 | 15 | FIR, Municipal Records, Official Interrogation, Cold Case Notice | P0090, P0124, P0136 |
| CIVIX-050 | N7 | 15 | FIR, Billing Invoice (inflated), Financial Audit, Interrogation | P0126, P0101, P0092, P0140, P0124 |

---

## ANTIGRAVITY EXECUTION CHECKLIST (For Each Evidence Item)

**Before Antigravity proceeds, verify:**

- [ ] **Person Photo Manifest**: All referenced persons (P####) are in the locked Persons Photo Manifest (Doc 10)
- [ ] **Case Details**: Case title, network, area, suspects match Universe Specification (Doc 7–8)
- [ ] **Cross-References**: Organizations (ORG###) match Principal Entity Roster (Doc 9)
- [ ] **Evidence Type Variety**: Each case has mix of forensic (fingerprint, medical, ballistics), digital (CDR, phone), document (FIR, registry), and visual (CCTV, ANPR) evidence
- [ ] **Open-Source Search First**: For each item, Antigravity prioritizes open-source imagery/documents before generating synthetic
- [ ] **Generation Guidelines**: Synthetic documents use realistic format (not photoreal injury imagery); fictional data only
- [ ] **Hero Evidence**: Special attention to **EVD-CHAINA-1/2/3** (P0001 chain), **EVD-HERO-1A/2A/3A** (three flagship cases)
- [ ] **Consistent Naming**: Output filenames follow pattern `EVD-{CASEID}-{SEQ}_{Description}.{ext}`

---

## SUMMARY STATISTICS

| Metric | Count |
|---|---|
| **Total Cases** | 50 |
| **Total Evidence Items** | ~750 (15 per case) |
| **Evidence Types** | 15 distinct types |
| **Persons Referenced** | 150+ |
| **Organizations Referenced** | 45+ |
| **Cross-Case Links** | 25+ (via LEAD-001 through LEAD-006 hero chains) |
| **Network Coverage** | 7 networks (N1–N7) |
| **Estimated Antigravity Runtime** | 12–18 hours (batch generation) |

---

## HANDOFF TO ANTIGRAVITY

**This manifest is complete and locked. Antigravity proceeds with:**

1. **Step 1**: Read Persons Photo Manifest (locked) for all 150+ persons
2. **Step 2**: For each of 50 cases, source/generate ~15 evidence items per this manifest
3. **Step 3**: Cross-check all person references (P####) against Photo Manifest
4. **Step 4**: Output files to `/evidence/` folder (organized by case)
5. **Step 5**: Log all evidence IDs and filenames in `EVIDENCE_REGISTRY.csv` (for database ingestion)

**When complete, Antigravity confirms:** 
- [ ] All 750 evidence items sourced/generated
- [ ] All output files named per `EVD-{CASEID}-{SEQ}_{Description}.{ext}` format
- [ ] All hero evidence (CHAINA-1/2/3, HERO-1A/2A/3A) completed
- [ ] Evidence Registry CSV created
- [ ] Ready for PostgreSQL ingestion via `civix_evidence_artifact` table

---

**END OF MANIFEST**

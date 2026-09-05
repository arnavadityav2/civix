# CIVIX 2.0 — EVIDENCE MANIFEST PART 2
## Version 1.0 — CIVIX-004 through CIVIX-055 (52 Cases × 15 Evidence Items = 780 Evidence Specifications)
**Completes: `CIVIX_2.0_CASES_EVIDENCE_MANIFEST.md` which covered only CIVIX-001 through CIVIX-003**
**Cross-Referenced Against: 02_Universe_Bible_Part2_CaseMatrix.md (canonical case specs)**

---

## NETWORK N1 — ARMED ROBBERY & LOGISTICS SYNDICATE (Cases CIVIX-004 through CIVIX-009)

---

### CIVIX-004: Armed Snatching Gang — NH-48 Corridor (2017)
**Status:** COLD | **Area:** NH-48 Highway Patrol Unit | **Suspects:** P0011, P0012
**Network:** N1 | **Opened:** 2017-02-12

#### EVD-004-001 — FIR PDF (Three Consolidated FIRs)
- **Type:** FIR_PDF
- **Description:** Three First Information Reports (FIR nos. 89, 90, 114/2017) filed at NH-48 Highway Patrol Unit for the series of 7 motorcycle snatching incidents between January and February 2017. Consolidated into single investigation file. Victims: P0303, P0304, P0305. Total loss: ₹4.2 lakh across all incidents.
- **Associated Persons:** P0011 (Kapil Dhankhar), P0303, P0304, P0305 (victims)
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create three consecutive FIR documents (NH-48 Highway Patrol), each dated Jan–Feb 2017. Include: FIR nos. 89, 90, 114/2017, suspect descriptions (2-3 motorcycle-borne men, masked), victim names, items snatched (motorcycles, valuables), total loss, location (NH-48 service road). Compiled into a single PDF with page breaks between FIRs.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-001_FIR_NH48_Snatching_3FIRs_89_90_114_2017.pdf

#### EVD-004-002 — CDR Dump (P0011 Registered Phone)
- **Type:** CDR_DUMP
- **Description:** Call Detail Record export from P0011's (Kapil Dhankhar's) registered phone number. Shows consistent pings to TOWER-NH-01 during 19:00–21:00 windows across multiple crime dates in January and February 2017. Tower proximity correlates to each of the 7 snatching locations on the NH-48 service road. This is the primary evidence placing P0011 at the crime zone.
- **Associated Persons:** P0011 (Kapil Dhankhar)
- **Associated Organizations:** BSNL/Airtel (telecom operator)
- **Prompt for Antigravity:** Generate: Create CDR CSV. Columns: [Call_Time, MSISDN, Tower_ID, Tower_Location, Event_Type]. Show 8 dates (7 crime dates + one non-crime date for comparison). On crime dates: tower = TOWER-NH-01, time window 18:30–21:30. Non-crime date: random Delhi tower. Include idle periods and SMS events. Realistic MSISDN format.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-004-002_CDR_P0011_DhankharPhone_NH48_2017.csv

#### EVD-004-003 — Victim Statements (Three Conflicting)
- **Type:** WITNESS_STATEMENT
- **Description:** Statements from victims P0303, P0304, P0305 recorded by NH-48 Highway Patrol. All three describe 2-3 male motorcycle riders, but height/build descriptions conflict: P0303 says one suspect was "tall and thin," P0304 says "medium height, stocky," P0305 describes "short, wore red jacket." Conflicts reduce evidentiary value but establish the pattern of crime.
- **Associated Persons:** P0303 (victim 1), P0304 (victim 2), P0305 (victim 3), P0011 (suspect described)
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create three separate witness statement forms (typed). Each: victim name, FIR reference, Q&A format, physical description of suspects (intentionally contradicting across three statements as described above), incident time/location, items stolen, victim signature, date (Jan–Feb 2017). Stamp: "Statement recorded at NH-48 Highway Patrol."
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-003_Witness_Statements_3Victims_Conflicting.pdf

#### EVD-004-004 — Bail Order (P0011 Released)
- **Type:** COURT_ORDER
- **Description:** Court order granting bail to P0011 (Kapil Dhankhar) after his initial arrest. Conditions: ₹20,000 personal bond, weekly police reporting. P0011 subsequently failed to report and absconded. This document establishes the legal history and the failure of the bail condition that created the absconder status.
- **Associated Persons:** P0011 (Kapil Dhankhar)
- **Associated Organizations:** NH-48 Highway Patrol Unit, Metropolitan Magistrate Court
- **Prompt for Antigravity:** Generate: Create a court bail order document. Include: case number, accused name (Kapil Dhankhar, P0011), date of arrest, offenses charged (robbery, IPC 392), bail conditions (₹20,000 bond, weekly reporting to NH-48 unit), date granted (Feb 2017), magistrate name and seal. Note at bottom: "Accused failed to appear for reporting on [date]. Non-bailable warrant issued."
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-004_Bail_Order_P0011_Dhankhar_NBW.pdf

#### EVD-004-005 — Non-Bailable Warrant (P0011 Absconder)
- **Type:** COURT_ORDER
- **Description:** Non-Bailable Warrant (NBW) issued against P0011 (Kapil Dhankhar) after he failed to appear for weekly bail reporting. Warrant remains active. P0011's last known address (Najafgarh) was searched; family confirmed he left without notice.
- **Associated Persons:** P0011 (Kapil Dhankhar)
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create a Non-Bailable Warrant document. Include: warrant number, accused name (Kapil Dhankhar), case number, grounds (failure to comply with bail conditions), issued by (Metropolitan Magistrate), directed to (Station House Officer, NH-48 Unit), date issued, seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-005_NBW_P0011_Dhankhar_Active.pdf

#### EVD-004-006 — CCTV Still (Partial Face, NH-48 Toll)
- **Type:** CCTV_CLIP
- **Description:** Single still frame from NH-48 toll plaza camera showing two motorcycles in convoy at 19:45 on one of the crime dates. Image quality: 480p, night mode IR (grainy). One rider's face partially visible, helmet partially raised. Frame captured 12 minutes before the nearest snatching incident.
- **Associated Persons:** P0011, P0012 (as unidentified figures on motorcycles)
- **Associated Organizations:** NH-48 Toll Authority
- **Prompt for Antigravity:** Generate: Create a 480p grainy night-vision CCTV still. Scene: toll gate, two motorcycles in single file, front rider's face partially visible (helmet partly raised, profile view). Timestamp overlay: 19:45, date in Jan–Feb 2017. Toll gate barriers visible in background. Monochrome/near-IR quality.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-004-006_CCTV_NH48_Toll_2017_Motorcycles_Partial.jpg

#### EVD-004-007 — Motorcycle Registration (P0011's Registered Bike)
- **Type:** VEHICLE_SEIZURE
- **Description:** Registration certificate for P0011's registered motorcycle (Hero Splendor, HR-25-AB-4512). Vehicle was never seized — P0011 absconded with it. RC shows registration to P0011's Najafgarh address. CDR tower TOWER-NH-01 triangulates this motorcycle as present at all 7 crime locations.
- **Associated Persons:** P0011 (Kapil Dhankhar)
- **Associated Organizations:** Haryana Transport Department
- **Prompt for Antigravity:** Generate: Create motorcycle RC document (Haryana format). Include: registration no. HR-25-AB-4512, owner name (Kapil Dhankhar), address (Najafgarh), vehicle make/model (Hero Splendor), engine/chassis no., registration date, insurance expiry. Haryana Transport Department letterhead.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-007_RC_Hero_Splendor_HR-25-AB-4512_P0011.pdf

#### EVD-004-008 — Police Lookout Notice (P0011)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Delhi/Haryana Police inter-state lookout circular issued for P0011 (Kapil Dhankhar, bail absconder). Includes physical description (last known: 5'9", slim, light complexion), motorcycle registration, and last known address. Circulated to all NCR and Haryana police stations.
- **Associated Persons:** P0011 (Kapil Dhankhar)
- **Associated Organizations:** NH-48 Highway Patrol, Delhi Police HQ
- **Prompt for Antigravity:** Generate: Create a police lookout circular. Include: suspect name (Kapil Dhankhar), alias if any, physical description, last known address (Najafgarh), vehicle details (Hero Splendor HR-25-AB-4512), offense (bail absconder, robbery), FIR reference, contact police station, date issued, police department stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-008_Lookout_Circular_P0011_Dhankhar.pdf

#### EVD-004-009 — Informant Report (P0011 Associates)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Confidential informant report (handler: NH-48 Patrol SHO) indicating that P0011 has known associates operating in Kuldeep Meena's robbery network (connecting to CIVIX-002). Informant states P0011 was "introduced to the Uttam Nagar group by a mutual contact." Confidence: LOW (single informant, unverified).
- **Associated Persons:** P0011, P0069 (Kuldeep Meena network associate in CIVIX-002)
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create a police informant report (internal memo format). Redact informant name/identity. Include: handler name (SHO, NH-48), date, intelligence received, content summary ("P0011 associates with Uttam Nagar robbery group"), confidence level (LOW), recommended action (surveillance of Uttam Nagar network), file reference.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-009_Informant_Report_P0011_Associates.pdf

#### EVD-004-010 — Victim Property Inventory (Combined Loss)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Combined inventory of property stolen across all 7 incidents. Items include: 5 motorcycles (various models), 7 mobile phones, ₹38,000 cash, one gold chain (10 grams). Total estimated loss: ₹4.2 lakh. Compiled by NH-48 patrol from all victim statements. Submitted to court with FIRs.
- **Associated Persons:** P0303, P0304, P0305 (primary three who filed FIRs; 4 others settled informally)
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create a consolidated property loss inventory (typed, police format). Include: itemized list (5 motorcycles with make/model/est. value, 7 phones, cash, jewelry), total estimated value (₹4,20,000), victims referenced, FIR reference numbers, date, prepared by officer, station stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-010_Property_Inventory_7Incidents_Total_4.2L.pdf

#### EVD-004-011 — Tower Analysis Map (TOWER-NH-01 Zone)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Spatial analysis map showing all 7 crime locations plotted against TOWER-NH-01 coverage zone. All incidents fall within the 800m radius of TOWER-NH-01. Map produced by CIVIX spatial intelligence module as part of pattern-of-crime analysis. Demonstrates P0011's consistent presence in the crime zone using CDR data.
- **Associated Persons:** P0011 (P0011's CDR tower data)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: Create a spatial analysis map (A4, clean layout). Background: NH-48 service road stretch, satellite or schematic style. Show: TOWER-NH-01 location with 800m radius circle, 7 incident markers numbered 1-7 (all inside the circle), crime dates annotated. Title: "CIVIX Spatial Analysis — TOWER-NH-01 Crime Cluster." Include compass, scale bar.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-004-011_CIVIX_Spatial_TowerNH01_CrimeCluster_Map.png

#### EVD-004-012 — Associate Background Check (P0012 Unknown Male)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** NH-48 Patrol investigation notes on attempts to identify P0012 (Unknown Male 2, P0011's accomplice). Notes detail: inquiries at Najafgarh and Dwarka police stations, query to state criminal database (no match on sketch), and one informant tip (unverified) suggesting the accomplice may be from Haryana's Rewari district.
- **Associated Persons:** P0012 (Unknown Male 2)
- **Associated Organizations:** NH-48 Highway Patrol, Haryana Police Rewari
- **Prompt for Antigravity:** Generate: Create internal investigation notes (handwritten-style scan). Include: date range (Feb–Mar 2017), steps taken (database queries, informant contact, inter-state inquiry), findings ("No match in Delhi/Haryana database. Informant tip: possible Rewari origin, unverified."), investigating officer name, case reference.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-012_Investigation_Notes_P0012_Unknown_Accomplice.pdf

#### EVD-004-013 — Case Diary (Cold Status)
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Case diary entry (NH-48 Patrol, 2018-02-12 — one year after opening) recording the case's transition to COLD status. Entry notes: "P0011 remains at large. P0012 unidentified. No new leads. NBW active. Case transferred to cold case register pending fresh intelligence."
- **Associated Persons:** P0011, P0012
- **Associated Organizations:** NH-48 Highway Patrol Unit
- **Prompt for Antigravity:** Generate: Create a case diary page (typed, police format). Date: 2018-02-12. Content: summary of investigation steps taken, current status of suspects (P0011 absconded, P0012 unidentified), NBW status, decision to transfer to cold case register, investigating officer signature, SHO countersignature.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-004-013_Case_Diary_COLD_Status_2018-02-12.pdf

#### EVD-004-014 — Cross-Case Link Document (CIVIX-002 P0011 Associates)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX-generated entity relationship note documenting the confirmed common associate link between P0011 (CIVIX-004) and Kuldeep Meena's network (CIVIX-002). Based on informant report EVD-004-009 and CDR pattern comparison. Confidence: LOW (0.31). Flagged for investigator review.
- **Associated Persons:** P0011, P0069 (CIVIX-002)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: Create a CIVIX intelligence report (system-formatted text/PDF). Include: lead reference (LEAD-004-X), relationship type (KNOWN_ASSOCIATE, LOW confidence 0.31), entities (P0011 ↔ P0069), evidence sources (informant report, CDR comparison), recommendation ("Monitor P0069 for P0011 contact; verify informant tip"). System timestamp.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-004-014_CIVIX_CrossCase_P0011_P0069_Associate_Link.pdf

#### EVD-004-015 — CIVIX Pattern-of-Crime Analysis Report
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX auto-generated pattern of crime report for the CIVIX-004 series. Identifies: temporal clustering (19:00–21:00 window, 94% of incidents), spatial clustering (all within 1.2 km of TOWER-NH-01), MO consistency (motorcycle teams, highway service road, 2-3 offenders). Recommends: targeted patrol of NH-48 service road 19:00–21:30 window with ANPR deployment.
- **Associated Persons:** P0011, P0012
- **Associated Organizations:** CIVIX System, NH-48 Highway Patrol
- **Prompt for Antigravity:** Generate: Create a CIVIX pattern analysis report. Include: case series (CIVIX-004, 7 incidents), temporal analysis chart (bar chart showing incident time distribution, peak 19:00–21:00), spatial cluster visualization (map reference), MO summary, confidence score (0.89 for pattern consistency), operational recommendation (patrol deployment). System-generated format.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-004-015_CIVIX_PatternOfCrime_NH48_Snatching_Analysis.pdf

---

### CIVIX-005: Loot of Bank Cash-in-Transit — Dwarka Sector 23 (2017)
**Status:** ACTIVE | **Area:** Dwarka PS | **Suspects:** P0013, P0014
**Network:** N1 | **Opened:** 2017-07-06

#### EVD-005-001 — CCTV Still (CAM-01, Partial Face P0013)
- **Type:** CCTV_CLIP
- **Description:** Still frame from CAM-01 (Dwarka Sector 23 market camera) captured on 2017-07-06 at 10:22. Shows one suspect (P0013, Vikas Gurjar) with partial face exposure — helmet visor partially raised, 40% confidence match. This is the primary identification evidence for P0013. Image extracted from 4-minute CCTV clip.
- **Associated Persons:** P0013 (Vikas Gurjar — partial face)
- **Associated Organizations:** Dwarka PS (evidence custodian)
- **Prompt for Antigravity:** Generate: Create a 2017-era CCTV still (480p, daytime, slightly grainy). Scene: street market, motorcyclist with helmet, visor 40% raised showing partial face (forehead, partial eyes, nose visible). Include: CAM-01 timestamp overlay (2017-07-06 10:22:17), camera ID (CAM-01), GPS coordinates of camera. Note in corner: "Face Match: 40% confidence."
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-001_CCTV_CAM01_P0013_Partial_Face_2017-07-06.jpg

#### EVD-005-002 — FIR PDF (No. 412/2017)
- **Type:** FIR_PDF
- **Description:** First Information Report filed at Dwarka PS, FIR No. 412/2017, for armed robbery of ICICI cash van on 2017-07-06. Three suspects, two motorcycles. ₹38 lakh looted. FIR notes: same location as 2012 robbery (CIVIX-001) — raised suspicion of insider knowledge of van route. Two suspects identified from CCTV: P0013 (partially) and P0014 (vehicle). One suspect absconding.
- **Associated Persons:** P0013 (Vikas Gurjar), P0014 (Hardeep Mann)
- **Associated Organizations:** Dwarka PS, ICICI Bank
- **Prompt for Antigravity:** Generate: Create Dwarka PS FIR No. 412/2017. Date: 2017-07-06. Include: location (Dwarka Sector 23 T-junction, same as 2012 case), MO (three suspects, two motorcycles, ICICI cash van, armed robbery), stolen amount (₹38 lakhs), suspect identification (partial CCTV), note re: same location as prior case, investigating officer name.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-002_FIR_Dwarka_PS_412_2017_CashVan.pdf

#### EVD-005-003 — Witness Statement (P0306 — Surveillance Observation)
- **Type:** WITNESS_STATEMENT
- **Description:** Statement from P0306 (Manoj Kumar Jha, auto-rickshaw driver) describing seeing a man matching P0013's description loitering near the SBI/ICICI cash point in January 2017 — 5 months before the robbery. P0306 states the man appeared to be noting down the van's arrival times. This establishes the EVENT-030 surveillance observation referenced in the case matrix.
- **Associated Persons:** P0306 (Manoj Kumar Jha, witness), P0013 (observed person)
- **Associated Organizations:** Dwarka PS
- **Prompt for Antigravity:** Generate: Create witness statement (police format). Witness: Manoj Kumar Jha, auto-rickshaw driver, Dwarka Sector 23 stand. Statement: "Around 14 January 2017, I noticed a man sitting near the cash van arrival point for two days in a row. He appeared to be writing something when the van arrived. He was wearing dark blue jacket." Photo ID of observer attached. Date: 2017-07-07, Dwarka PS.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-003_Witness_Statement_P0306_Surveillance_Observation.pdf

#### EVD-005-004 — CDR Analysis (P0013 Proximity)
- **Type:** CDR_DUMP
- **Description:** CDR analysis for P0013's (Vikas Gurjar's) phone showing tower pings near Dwarka Sector 23 (TOWER-DW-02) on 2017-07-05 (eve of robbery) from 14:00–16:30. Day of robbery (2017-07-06): phone switched off 09:30–12:00 (robbery window was 10:22). Phone reactivated 12:15 in Najafgarh area. Pattern consistent with deliberate phone discipline during crime.
- **Associated Persons:** P0013 (Vikas Gurjar)
- **Associated Organizations:** Airtel (telecom)
- **Prompt for Antigravity:** Generate: Create CDR extract (tabular, CSV-style). Show: 2017-07-05 (14:00–16:30, TOWER-DW-02 pings), 2017-07-06 (09:30 — last ping TOWER-DW-01, then 4-hour gap, 13:15 — ping TOWER-NJ-01 Najafgarh). Include call events with duration, tower ID, location description. Note gap in activity (phone off or in Faraday cage 09:30–13:15 on crime day).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-004_CDR_P0013_Gurjar_TowerProximity_CrimeDay.csv

#### EVD-005-005 — Chargesheet (P0013)
- **Type:** COURT_ORDER
- **Description:** Police chargesheet filed against P0013 (Vikas Gurjar) by Dwarka PS. Charges: IPC 392 (robbery), 397 (robbery with harm), 34 (common intention). Evidence basis: 40% CCTV match (EVD-005-001), CDR data (EVD-005-004), witness statement (EVD-005-003). Case pending trial. P0014 listed as accused at large.
- **Associated Persons:** P0013 (Vikas Gurjar — chargesheeted), P0014 (Hardeep Mann — absconding)
- **Associated Organizations:** Dwarka PS, Metropolitan Court
- **Prompt for Antigravity:** Generate: Create police chargesheet document. Include: case number (FIR 412/2017), accused (P0013, P0014), charges (IPC sections listed), evidence summary (CCTV 40%, CDR, witness), IO certification, court submission date, additional accused note (P0014 absconding, lookout issued).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-005_Chargesheet_P0013_Gurjar_FIR412_2017.pdf

#### EVD-005-006 — Bank Internal Route Document (ICICI)
- **Type:** FINANCIAL_STATEMENT
- **Description:** ICICI Bank internal cash-in-transit schedule for Dwarka Sector 23 route on 2017-07-06. Shows the cash van's scheduled pickup time (10:15–10:30 window), the amount authorized for transport (₹38 lakhs), and the route. This document, combined with the witness surveillance observation (EVD-005-003), supports Hypothesis H-005-B (insider knowledge of van schedule).
- **Associated Persons:** P0013 (suspected to have had prior knowledge), bank manager (fictional)
- **Associated Organizations:** ICICI Bank, Dwarka Branch
- **Prompt for Antigravity:** Generate: Create ICICI Bank internal memo (cash-in-transit operations, dated 2017-07-04 — 2 days before robbery). Include: route schedule (Dwarka Sector 23 pickups, times, amounts), vehicle registration, driver name (fictional), security detail. Stamped "CONFIDENTIAL — INTERNAL USE ONLY." This would have been the leaked document.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-006_ICICI_Bank_CIT_Route_Schedule_2017-07-06.pdf

#### EVD-005-007 — ANPR Crop (Motorcycle Plate)
- **Type:** ANPR_CROP
- **Description:** ANPR system crop from Dwarka Sector 17 camera showing one of the two motorcycles used in the robbery (partially visible plate: HR-07-??-????). Plate partially obscured by mud. Captured at 10:08 on 2017-07-06 — 14 minutes before the robbery.
- **Associated Persons:** P0013 or P0014 (rider on this motorcycle)
- **Associated Organizations:** Dwarka PS, Dwarka Traffic Police
- **Prompt for Antigravity:** Generate: ANPR detection image. Motorcycle front-on at camera angle. License plate: HR-07-XX-XXXX with last 6 characters obscured by mud. Timestamp: 2017-07-06 10:08, camera ID DWK-17-ANPR-01. Confidence: 34% (partial plate). Traffic camera overlay.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-007_ANPR_Motorcycle_Partial_HR07_2017-07-06.png

#### EVD-005-008 — Lookout Circular (P0014 Absconding)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Inter-state lookout circular for P0014 (Hardeep Mann, SUSPECT, ABSCONDING). Last known address: Gurugram. Photo description from CCTV: tall male, heavy build, dark complexion. Motorcycle: DL-registered bike (partial plate from ANPR). Circulated to Punjab, Haryana, Himachal Pradesh police.
- **Associated Persons:** P0014 (Hardeep Mann)
- **Associated Organizations:** Dwarka PS, Delhi Police HQ, Punjab/Haryana Police
- **Prompt for Antigravity:** Generate: Create inter-state lookout circular for P0014. Include: name, alias (unknown), last known address (Gurugram), physical description (tall, heavy, dark complexion), vehicle details (DL-registration motorcycle, partial plate), offenses, FIR reference, reward if any, contact station.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-008_Lookout_Circular_P0014_HardeepMann_Interstate.pdf

#### EVD-005-009 — Hypothesis Scoring Document (H-005-B Insider)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX hypothesis scoring document for H-005-B: "An SBI/ICICI insider leaked the cash van schedule." Score: 0.52 (POSSIBLE). Supporting evidence: same location as 2012 robbery (CIVIX-001), witness surveillance observation 5 months prior (EVD-005-003), bank route document specificity. Contradicting: no direct evidence of insider contact; robbers may have simply revisited a previously successful location.
- **Associated Persons:** P0013 (suspect who may have been fed information), bank staff (unidentified potential insider)
- **Associated Organizations:** CIVIX System, ICICI Bank
- **Prompt for Antigravity:** Generate: Create CIVIX hypothesis evaluation card. Include: hypothesis ID (H-005-B), text ("SBI/ICICI insider leaked van schedule"), score (0.52 POSSIBLE), supporting evidence list (3 items), contradicting evidence list (2 items), recommended actions ("Interview all ICICI Dwarka staff with access to CIT schedule", "Cross-check personnel with CIVIX-001 Dwarka staff records"), system timestamp.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-009_CIVIX_Hypothesis_H005B_Insider_Score0.52.pdf

#### EVD-005-010 — Medical Report (Injured Guard)
- **Type:** MEDICAL_REPORT
- **Description:** Medical examination report for the ICICI cash van guard injured during the robbery. Injuries: blunt trauma to head (suspected baton strike), minor lacerations on left arm. Examined at Dwarka Government Hospital, 2017-07-06. Guard hospitalized for 3 days. Injuries consistent with assault, not accidental.
- **Associated Persons:** Cash van guard (fictional, VICTIM)
- **Associated Organizations:** Dwarka Government Hospital, ICICI Bank, Dwarka PS
- **Prompt for Antigravity:** Generate: Create a medical examination report. Include: patient name (fictional guard), date (2017-07-06), examining physician, injuries (blunt head trauma, arm lacerations), mechanism consistent with baton/blunt weapon, GSR negative, discharge date (2017-07-09), clinical conclusions, hospital stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-010_Medical_Report_Guard_Injured_2017-07-06.pdf

#### EVD-005-011 — ICICI Bank Insurance Claim
- **Type:** FINANCIAL_STATEMENT
- **Description:** ICICI Bank insurance claim for ₹38 lakh stolen from the cash van. Filed with their cargo-in-transit insurer within 24 hours. Claim includes: incident report, police FIR reference, guard medical report, and preliminary assessment of loss. Insurer dispatched loss assessor within 48 hours.
- **Associated Persons:** ICICI Bank manager (fictional)
- **Associated Organizations:** ICICI Bank, Insurance Company
- **Prompt for Antigravity:** Generate: Create insurance claim form (ICICI Bank letterhead, dated 2017-07-07). Include: claim no., amount (₹38,00,000), incident date/location, FIR reference (412/2017), attached documents list, insurance policy number, authorized signatory.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-011_Insurance_Claim_ICICI_38L_2017.pdf

#### EVD-005-012 — Reconstruction Diagram (Crime Scene)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Crime scene reconstruction diagram prepared by Dwarka PS after initial investigation. Shows: cash van stopping point, two motorcycles' approach vectors, suspect positions, escape route (via Sector 23 internal road toward Uttam Nagar). Drawn by investigating officer, signed by SHO.
- **Associated Persons:** P0013, P0014 (positions in diagram)
- **Associated Organizations:** Dwarka PS
- **Prompt for Antigravity:** Generate: Create a hand-drawn (or simple CAD) crime scene reconstruction diagram (A4). Show: road layout (T-junction), cash van position, two motorcycles approaching from east, suspect positions (numbered 1, 2, 3), escape route arrows (south toward Sector 17), CCTV camera CAM-01 position. Legend, north arrow, scale bar, investigating officer name, date (2017-07-07).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-012_CrimeScene_Reconstruction_Diagram_CIVIX005.pdf

#### EVD-005-013 — Suresh Valmiki Connection (Cross-Case Link)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX entity link document connecting CIVIX-005 to CIVIX-009 via Suresh Valmiki (P0001). Dwarka PS investigator discovered P0013 (Vikas Gurjar) was previously arrested alongside P0001 in a 2015 minor case (common accused). This provides a confirmed prior associate link between the 2017 robbery (CIVIX-005) and the 2026 arrest (CIVIX-009).
- **Associated Persons:** P0013 (Vikas Gurjar), P0001 (Suresh Valmiki)
- **Associated Organizations:** CIVIX System, Dwarka PS
- **Prompt for Antigravity:** Generate: Create a CIVIX entity relationship report. Include: source entity (P0013 Vikas Gurjar), target entity (P0001 Suresh Valmiki), relationship type (PRIOR_COMMON_ACCUSED), evidence basis (2015 minor case, Dwarka PS records), confidence (0.72 HIGH), cross-case reference (CIVIX-005 ↔ CIVIX-009). System format.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-013_CIVIX_Entity_Link_P0013_P0001_PriorCase.pdf

#### EVD-005-014 — Property Seizure Report (Abandoned Vehicle)
- **Type:** VEHICLE_SEIZURE
- **Description:** Report of abandoned motorcycle (HR-07-AZ-2341) found in Uttam Nagar back lane, 2017-07-06 at 17:30. Vehicle matches one of the two escape motorcycles based on eyewitness description (blue-black Honda Shine, similar specs). Fingerprints lifted from handlebar; no database match in 2017. Vehicle seized and stored at Dwarka PS evidence depot.
- **Associated Persons:** P0013 or P0014 (suspected rider)
- **Associated Organizations:** Dwarka PS, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create a vehicle seizure/abandonment report (police form). Include: vehicle description (Honda Shine, blue-black, HR-07-AZ-2341), location found (Uttam Nagar back lane), date/time (2017-07-06 17:30), seizing officer, fingerprint collection status (collected, no match 2017), storage location (Dwarka PS depot).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-005-014_Seized_Vehicle_Abandoned_HR-07-AZ-2341_2017.pdf

#### EVD-005-015 — CIVIX Lead Report (Suresh Valmiki Reconnection)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX auto-generated investigative lead (LEAD-005-B) generated in 2026 after P0001 (Suresh Valmiki) arrest in CIVIX-009. System flags P0013 (CIVIX-005) as P0001's prior associate, recommending investigators check whether P0013 participated in 2026 robbery. Score: 0.68 (HIGH). Cross-case link: CIVIX-005 ↔ CIVIX-009.
- **Associated Persons:** P0001, P0013
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: CIVIX lead report. Lead ID: LEAD-005-B. Generated: 2026-07-19 (day of P0001 arrest). Content: "P0013 Vikas Gurjar is a confirmed prior associate of P0001. P0013's current whereabouts unknown. Recommend: check P0013's CDR for 2026-07-19 tower presence near Najafgarh. Cross-case: CIVIX-005, CIVIX-009." Score: 0.68. Priority: HIGH.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-005-015_CIVIX_Lead_LEAD005B_P0013_P0001_Connection.pdf

---

### CIVIX-006: Firearm Recovery & Robbery Conspiracy — Uttam Nagar (2011)
**Status:** OPEN | **Area:** Uttam Nagar PS | **Suspects:** P0015, P0016, P0017
**Network:** N1 | **Opened:** 2011-08-27

#### EVD-006-001 — Ballistics Report (Country-Made Pistols)
- **Type:** BALLISTICS_REPORT
- **Description:** Forensic ballistics report for two country-made pistols (filed serial numbers) recovered from P0015's (Santosh Mishra's) house during tenant verification drive. Each pistol tested: both functional, firing .315 bore ammunition. Weapon origin traceable to Bihar by barrel rifling marks (consistent with known Bihar manufacturer patterns). Serial numbers filed off — partial trace possible via rifling database.
- **Associated Persons:** P0015 (Santosh Mishra — original weapon holder, deceased 2019)
- **Associated Organizations:** Uttam Nagar PS Ballistics Lab
- **Prompt for Antigravity:** Generate: Create ballistics report (2011, lab format). Include: evidence items (2 pistols, serial filed), weapon type (country-made .315 bore), functional test result (both operational), rifling analysis (Bihar-pattern manufacturing), test-fire results, examiner name, date (2011-08-28), lab seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-001_Ballistics_CountryMadePistols_Bihar_2011.pdf

#### EVD-006-002 — Recovered Chit (Handwritten Robbery Plan)
- **Type:** FORENSIC_AUDIT
- **Description:** Handwritten paper chit recovered from the same house, partially burned. Legible portion shows: a location name (Uttam Nagar main road), time window (22:00), and the words "gaadi roke" (stop the vehicle). Handwriting analysis confirmed as P0015's. Chit establishes conspiracy for a robbery that was never executed. This is the key conspiracy evidence.
- **Associated Persons:** P0015 (Santosh Mishra — writer confirmed by handwriting analysis)
- **Associated Organizations:** Uttam Nagar PS, CFSL (Central Forensic Science Laboratory)
- **Prompt for Antigravity:** Generate: Create a forensic document examination exhibit. Show: photograph of partially burned paper chit (legible portion highlighted), Hindi text transcription ("gaadi roke" and location), English translation, CFSL handwriting analyst report excerpt confirming P0015 as writer, confidence level. Date: 2011-09-05, CFSL report number.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-002_Chit_RobberyPlan_Handwritten_P0015_CFSL.pdf

#### EVD-006-003 — FIR (No. 634/2011)
- **Type:** FIR_PDF
- **Description:** FIR No. 634/2011 filed at Uttam Nagar PS for illegal arms possession and criminal conspiracy. Filed following the tenant verification drive. Suspects: P0015 (arms holder), P0016 (wife, claims ignorance), and P0017 (Bihar arms supplier, unidentified). No robbery occurred; charges based on recovery and chit evidence.
- **Associated Persons:** P0015 (Santosh Mishra), P0016 (Deepa Mishra), P0017 (unidentified supplier)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create Uttam Nagar PS FIR No. 634/2011. Date: 2011-08-27. Include: tenant verification context (how weapons were found), weapon description (2 pistols, 11 cartridges), chit conspiracy evidence, accused names, charges (Arms Act + IPC 120B conspiracy), investigating officer.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-003_FIR_Uttam_Nagar_634_2011_ArmsRecovery.pdf

#### EVD-006-004 — Tenant Verification Form (Discovery Context)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Police tenant verification form filled by Santosh Mishra (P0015) declaring occupation as "daily wage labor." Form triggered routine police check (every tenant required to file within 30 days of moving). During the verification visit, the constable noticed bulge in almirah; P0015 consented to search. Weapons discovered. Verification form establishes the legal basis for the search.
- **Associated Persons:** P0015 (Santosh Mishra)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create tenant verification form (police format). Include: tenant name (Santosh Mishra), address, occupation declared (daily wage labor), date of filing, landlord name, police constable signature, date of visit (2011-08-27), finding note ("Weapons discovered during routine consent search").
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-004_Tenant_Verification_P0015_Discovery_Context.pdf

#### EVD-006-005 — Arms Seizure Report
- **Type:** VEHICLE_SEIZURE
- **Description:** Formal arms seizure report documenting recovery of 2 country-made pistols and 11 .315 cartridges from the residential premises. Includes chain-of-custody signature, seizure memo, inventory, and packaging for CFSL dispatch. Prepared by Uttam Nagar PS on 2011-08-27.
- **Associated Persons:** P0015 (Santosh Mishra), seizing constable
- **Associated Organizations:** Uttam Nagar PS, CFSL
- **Prompt for Antigravity:** Generate: Create arms seizure memo (police format). Include: location of seizure, items seized (list: 2 pistols — description, 11 cartridges — caliber), witness names, seizing officer, chain-of-custody signatures, packaging and CFSL dispatch memo, case reference FIR 634/2011.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-005_Arms_Seizure_Report_2Pistols_11Cartridges.pdf

#### EVD-006-006 — Deepa Mishra Statement (P0016)
- **Type:** WITNESS_STATEMENT
- **Description:** Statement from P0016 (Deepa Mishra, wife of P0015) recorded at Uttam Nagar PS. She claims: "I had no knowledge of the weapons. My husband worked in construction. He never discussed his activities. I signed papers he brought home without understanding them." Statement used as supporting evidence for her claim of ignorance. Status: PERSON_OF_INTEREST.
- **Associated Persons:** P0016 (Deepa Mishra), P0015 (Santosh Mishra)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create witness statement (police format). Witness: Deepa Mishra. Statement in Q&A: "Did you know about the weapons?" — "No, I never saw them. He kept the almirah locked." "Did you sign any papers recently?" — "Yes, he gave me some papers to sign, said it was for the house." Signature, date (2011-08-28), PS stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-006_Statement_P0016_DepaMishra_ClaimsIgnorance.pdf

#### EVD-006-007 — Bihar Arms Supplier Trace (Partial)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Inter-state intelligence trace attempting to identify P0017 (Bihar Arms Supplier). Delhi Police requested Bihar Police to investigate the weapon's origin based on rifling marks. Bihar Police response: rifling pattern consistent with Munger district illegal gun makers. No specific manufacturer identified. Request for further cooperation sent but case not pursued aggressively.
- **Associated Persons:** P0017 (Bihar arms supplier — unidentified)
- **Associated Organizations:** Uttam Nagar PS, Bihar Police (Munger district)
- **Prompt for Antigravity:** Generate: Create inter-state police correspondence (letter format). Delhi Police requesting Bihar Police assistance in tracing weapon manufacturer based on rifling marks. Bihar Police response letter: "Pattern consistent with Munger district craft manufacture. Unable to identify specific unit without further evidence." Both letters on respective letterheads.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-007_Inter_State_Arms_Trace_Bihar_Munger.pdf

#### EVD-006-008 — Cartridge Analysis Report
- **Type:** FORENSIC_AUDIT
- **Description:** CFSL analysis of 11 recovered .315 bore cartridges. All unfired. Headstamp examination reveals mixed batch: 6 cartridges from legitimate commercial manufacturer, 5 from unlicensed source (headstamp inconsistencies, manufacturing defects). The mixed batch is consistent with purchases from an illegal arms dealer who sources from multiple origins.
- **Associated Persons:** P0015 (Santosh Mishra), P0017 (Bihar supplier)
- **Associated Organizations:** CFSL, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create CFSL cartridge examination report. Include: 11 cartridges examined (numbered C1-C11), headstamp analysis (describe commercial vs. non-standard markings), manufacturing defect notes (5 cartridges), origin assessment, examiner name, date (2011-09-10), CFSL report number.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-008_CFSL_Cartridge_Analysis_315Bore_MixedBatch.pdf

#### EVD-006-009 — Death Certificate (P0015, 2019)
- **Type:** MEDICAL_REPORT
- **Description:** Death certificate for P0015 (Santosh Mishra), deceased 2019 (natural causes — cardiac arrest). Case against P0015 abated upon death; case remains OPEN against P0016 (cleared on merits) and P0017 (unidentified). This document formally closes the P0015 thread while keeping the case open for the Bihar supplier angle.
- **Associated Persons:** P0015 (Santosh Mishra, deceased)
- **Associated Organizations:** Delhi Municipal Corporation
- **Prompt for Antigravity:** Generate: Create death certificate (DMC format). Include: deceased name (Santosh Mishra), date of death (2019, approximate month), cause (cardiac arrest), certified by, place of death (Delhi). NABL stamp. Note: not photorealistic person — clinical document only.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-009_Death_Certificate_P0015_SantoshMishra_2019.pdf

#### EVD-006-010 — Case Status Update (P0015 Abatement)
- **Type:** COURT_ORDER
- **Description:** Court order recording abatement of proceedings against P0015 (Santosh Mishra) following his death in 2019. Case continues against P0017 (unidentified Bihar supplier) as a named-but-unidentified accused. Court directs police to "make fresh efforts to identify and apprehend the Bihar arms supplier."
- **Associated Persons:** P0015 (abated), P0017 (case continues)
- **Associated Organizations:** Metropolitan Magistrate Court, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create court order recording abatement. Include: case number (FIR 634/2011), note of P0015 death (with death certificate reference), legal effect (proceedings abated against P0015), continuing direction (P0017 — identify and apprehend), date of order, magistrate name and seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-010_Court_Abatement_P0015_2019_CaseContinues.pdf

#### EVD-006-011 — Cross-Case Ballistics Link (CIVIX-020)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX-generated ballistics cross-case link. CFSL ballistics database comparison finds the rifling marks from CIVIX-006 pistols are consistent with weapons recovered in CIVIX-020 (Karol Bagh plate cloning case, where a firearm was also recovered). Confidence: 0.63 (MODERATE). Suggests both cases may share the same Bihar arms supplier (P0017).
- **Associated Persons:** P0017 (Bihar supplier — linking entity across cases)
- **Associated Organizations:** CIVIX System, CFSL
- **Prompt for Antigravity:** Generate: CIVIX ballistics cross-case report. Include: source evidence (CIVIX-006 ballistics EVD-006-001), comparison evidence (CIVIX-020 firearm), comparison finding ("Rifling mark pattern similarity score: 0.63"), inference ("Common supply source possible — Bihar manufacturer P0017 unidentified"), recommendation ("Request CFSL formal comparison opinion").
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-006-011_CIVIX_CrossCase_Ballistics_006_020_BiharSupplier.pdf

#### EVD-006-012 — Deepa Mishra Acquittal Order
- **Type:** COURT_ORDER
- **Description:** Court order acquitting P0016 (Deepa Mishra) of all charges on grounds of insufficient evidence of knowledge or participation. Judge's reasoning: "Signing papers at husband's request without knowledge of their content does not constitute conspiracy." P0016 discharged. Her status changes to CLEARED.
- **Associated Persons:** P0016 (Deepa Mishra — acquitted)
- **Associated Organizations:** Metropolitan Magistrate Court
- **Prompt for Antigravity:** Generate: Create court acquittal order. Include: accused name (Deepa Mishra), case number, charges faced, judge's reasoning (lack of knowledge, no active participation), verdict (ACQUITTED), date, court seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-012_Acquittal_P0016_DepaMishra_Cleared.pdf

#### EVD-006-013 — CFSL Physical Examination (Weapon Condition)
- **Type:** FORENSIC_AUDIT
- **Description:** CFSL physical examination report on both seized pistols. Findings: both weapons show signs of recent use (barrel residue, firing pin wear), suggesting weapons were used in prior crimes before recovery. Residue analysis indicates: fired within 30 days of seizure. This is significant — weapons were in active use, not merely stored.
- **Associated Persons:** P0015 (Santosh Mishra — possessor)
- **Associated Organizations:** CFSL, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create CFSL physical examination report. Include: Exhibit A and B (two pistols), external condition (slight wear, residue in barrel), firing pin wear assessment (recent use confirmed), GSR swab of barrel interior (positive within 30-day threshold), examiner name, date, CFSL seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-006-013_CFSL_Physical_Exam_Pistols_RecentUse.pdf

#### EVD-006-014 — Uttam Nagar-Dwarka Corridor Analysis
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX spatial intelligence report analyzing the geographic relationship between CIVIX-006 (Uttam Nagar) and CIVIX-004 (NH-48 snatching). Both cases are in the same 4 km corridor (Uttam Nagar to NH-48 service road). The recovered weapons in CIVIX-006 match the caliber of weapons described in one CIVIX-004 victim statement (victim P0303 mentioned seeing a short firearm). Hypothesis: CIVIX-006 weapons may have been used in CIVIX-004 snatchings.
- **Associated Persons:** P0015, P0011 (potential weapon sourcing link)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: CIVIX spatial corridor analysis. Map showing Uttam Nagar (CIVIX-006) and NH-48 service road (CIVIX-004), 4 km distance. Hypothesis overlay: "Weapons recovered CIVIX-006 may be sourced for/used in CIVIX-004 snatchings (Confidence: LOW 0.28)." Evidence basis: caliber match, geographic proximity, time overlap (both 2011-2017).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-006-014_CIVIX_Spatial_Corridor_006_004_WeaponLink.png

#### EVD-006-015 — CIVIX Unsolved Lead Report (P0017 Trace)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX investigative lead (LEAD-006-A) generated in 2026 when the Bihar arms supplier (P0017) pattern is compared against newer Bihar-linked cases in the CIVIX database. System identifies a possible common supply chain linking CIVIX-006, CIVIX-020, and a 2024 arms recovery in Munger. Score: 0.44 (POSSIBLE). Flagged for Bihar Police liaison action.
- **Associated Persons:** P0017 (Bihar arms supplier — still unidentified)
- **Associated Organizations:** CIVIX System, Bihar Police
- **Prompt for Antigravity:** Generate: CIVIX lead report. Lead ID: LEAD-006-A. Generated: 2026. Content: "Pattern analysis: Bihar-origin arms supplier (P0017, unidentified) appears in CIVIX-006, CIVIX-020, and a new 2024 Munger case. Request Bihar Police provide suspect list for Munger illegal arms manufacturers." Score: 0.44, Priority: MEDIUM.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-006-015_CIVIX_Lead_LEAD006A_BiharSupplier_P0017.pdf

---

### CIVIX-007: Interstate Robbery Gang — Uttam Nagar Module (2013)
**Status:** COLD | **Area:** Uttam Nagar PS | **Suspects:** P0018, P0019, P0307
**Network:** N1 | **Opened:** 2013-01-09

#### EVD-007-001 — FIR (No. 23/2013)
- **Type:** FIR_PDF
- **Description:** FIR No. 23/2013 filed at Uttam Nagar PS for a series of 5 chain snatchings and 2 armed robberies attributed to an interstate gang from Rajasthan. Two suspects arrested (P0018 Ramkishan Bairwa and one other), three absconded including P0019 (Shyam Meena). P0018's testimony mentioned a "Delhi contact" known as "Suresh Ji" (P0307).
- **Associated Persons:** P0018 (Ramkishan Bairwa), P0019 (Shyam Meena), P0307 ("Suresh Ji" — unidentified)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create Uttam Nagar PS FIR No. 23/2013. Date: 2013-01-09. Include: 5 chain snatchings + 2 armed robberies summary, Rajasthan gang origin, arrested suspects (P0018, one other), absconding suspects (P0019 and 2 others), mention of "Delhi contact Suresh Ji" from P0018 statement.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-001_FIR_Uttam_Nagar_23_2013_Interstate_Gang.pdf

#### EVD-007-002 — Chargesheet with P0018 Testimony
- **Type:** COURT_ORDER
- **Description:** Police chargesheet against P0018 (Ramkishan Bairwa) and co-accused. Key element: P0018's testimony section explicitly mentions "Suresh Ji from Delhi — he arranged the buyers for our stolen goods and gave us advance money for jobs." This statement creates the identity candidate IC-003 — "Suresh Ji" = possibly Suresh Valmiki (P0001).
- **Associated Persons:** P0018 (Ramkishan Bairwa), P0307 ("Suresh Ji")
- **Associated Organizations:** Uttam Nagar PS, Metropolitan Court
- **Prompt for Antigravity:** Generate: Create police chargesheet. Include: accused names, charges, evidence summary. Key section: P0018 testimony extract — "There is a man in Delhi we called 'Suresh Ji'. He used to give advance money for jobs and helped sell stolen items." Highlight this testimony. Chargesheet submitted date, IO signature.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-002_Chargesheet_P0018_Testimony_SureshJi.pdf

#### EVD-007-003 — Conviction Order (P0018 — 5 Years)
- **Type:** COURT_ORDER
- **Description:** District Court conviction order for P0018 (Ramkishan Bairwa). Convicted of robbery, criminal conspiracy, inter-state crime. Sentence: 5 years rigorous imprisonment. P0018 served full sentence and was released circa 2018. The conviction document includes the "Suresh Ji" testimony as recorded evidence, preserving it for future use.
- **Associated Persons:** P0018 (Ramkishan Bairwa)
- **Associated Organizations:** Delhi District Court, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create district court conviction order. Include: case number (FIR 23/2013), accused (Ramkishan Bairwa), charges, verdict (CONVICTED), sentence (5 years rigorous imprisonment), fine if any, evidence relied upon including P0018 testimony re: "Suresh Ji", judge name, date of conviction, court seal.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-003_Conviction_P0018_Bairwa_5Years.pdf

#### EVD-007-004 — Rajasthan Police Liaison Note
- **Type:** INTELLIGENCE_REPORT
- **Description:** Correspondence between Uttam Nagar PS and Rajasthan Police (Bharatpur/Alwar district) regarding the interstate gang's origin. Rajasthan Police confirms: P0018 and P0019 are from Bharatpur district, known for motorcycle theft and chain snatching gangs. P0019 (Shyam Meena) has a prior case in Bharatpur (theft, 2010). Lookout issued.
- **Associated Persons:** P0018, P0019 (Shyam Meena)
- **Associated Organizations:** Uttam Nagar PS, Rajasthan Police Bharatpur
- **Prompt for Antigravity:** Generate: Create inter-police liaison correspondence. Uttam Nagar PS letter requesting Rajasthan background on accused. Rajasthan Police response: confirms Bharatpur origin of P0018 and P0019, mentions P0019's 2010 Bharatpur theft case, issues lookout for P0019. Two-letter format on respective letterheads.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-004_Interstate_Liaison_Rajasthan_P0018_P0019.pdf

#### EVD-007-005 — P0307 "Suresh Ji" Identity Candidate Report
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX identity candidate report (IC-003) for "Suresh Ji" (P0307). Analysis of P0018's testimony description of "Suresh Ji" against known persons in CIVIX database. Candidate match: P0001 (Suresh Valmiki) — age range match, Delhi-based, documented role in N1 network. Confidence: 0.41 (LOW — based on name and role description only). Flagged for investigator review.
- **Associated Persons:** P0307 ("Suresh Ji"), P0001 (Suresh Valmiki — candidate match)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: CIVIX IC report. IC-003. Entities compared: P0307 ("Suresh Ji" — description: Delhi-based male, middle-aged, broker/advance-money role) vs P0001 (Suresh Valmiki — Delhi, male, N1 network role documented). Match basis: name (Suresh, common), role (advance-money fixer), geography (Delhi). Score: 0.41, Status: LOW confidence. Note: requires investigator verification.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-005_CIVIX_IC003_SureshJi_P0307_Candidate.pdf

#### EVD-007-006 — Victim Statements (Chain Snatching Series)
- **Type:** WITNESS_STATEMENT
- **Description:** Compilation of victim statements from 5 chain snatching incidents. All describe: 2 motorcyclist attackers from behind, gold chain snatched at traffic light or slow stretch, immediate high-speed escape. Three victims saw partial face; descriptions consistent with Rajasthani male features (consistent with P0018/P0019 profiles). All incidents within 3 km radius.
- **Associated Persons:** P0018, P0019 (described suspects), multiple victims
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Compiled victim statement report (5 statements in one document). Each victim: name, date/time, location, items stolen (gold chain), suspect description (2 motorcyclists, one grabs chain). Consistent description elements highlighted across all 5 statements. Prepared by IO Uttam Nagar PS.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-006_Victim_Statements_5ChainSnatchings_Compiled.pdf

#### EVD-007-007 — CCTV Footage (Armed Robbery Scene)
- **Type:** CCTV_CLIP
- **Description:** CCTV clip from Uttam Nagar market area showing one of the two armed robberies. Quality: 360p 2013-era. Shows two motorcyclists approaching a pedestrian, one producing a firearm, pedestrian handing over bag, motorcyclists fleeing. Timestamp: 2013-01-09 21:15.
- **Associated Persons:** P0018, P0019 (as unidentified motorcycle riders)
- **Associated Organizations:** Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create 360p 2013-era CCTV still/clip. Scene: market lane, night, two motorcyclists approaching pedestrian, arm extended (weapon implied but not clearly visible), pedestrian stepping back, handing bag. Timestamp 2013-01-09 21:15. IR camera quality.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-007_CCTV_Uttam_Nagar_ArmedRobbery_2013-01-09.jpg

#### EVD-007-008 — Stolen Goods Recovery Report
- **Type:** VEHICLE_SEIZURE
- **Description:** Report of partial recovery of stolen goods from a Jaipur-based second-hand market (Rajasthan Police coordination). Two gold chains matching victim descriptions recovered from a reseller. Reseller claims purchased from a Bharatpur man matching P0018's description. Chains returned to victims P0303A and P0303B (fictional victim identifiers). Reseller not charged.
- **Associated Persons:** P0018 (seller identified by reseller), victims
- **Associated Organizations:** Rajasthan Police Jaipur, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Create property recovery report (Rajasthan Police Jaipur coordination). Include: items recovered (2 gold chains, weights/descriptions matching victim complaints), recovery location (Jaipur second-hand market), reseller statement ("bought from a Bharatpur man, medium height, pointed moustache"), chain of custody, transfer to Delhi PS.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-008_Stolen_Goods_Recovery_Jaipur_GoldChains.pdf

#### EVD-007-009 — P0019 Absconding Status Update (2026)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX system update on P0019 (Shyam Meena) absconding status in 2026. P0019 has been a registered bail absconder since 2013. CIVIX flags: no CDR activity traced to P0019's last known number (2013–2026). Possible scenarios: fled to Rajasthan, changed identity, or deceased. Status remains ABSCONDING. CIVIX recommends: cross-reference with Rajasthan CCTNS database.
- **Associated Persons:** P0019 (Shyam Meena)
- **Associated Organizations:** CIVIX System, Delhi Police Records Bureau
- **Prompt for Antigravity:** Generate: CIVIX status update report. Subject: P0019 (Shyam Meena), bail absconder since 2013. CDR analysis: no activity 2013–2026. Possible scenarios listed. Recommendation: Rajasthan CCTNS query, check border crossing records. Priority: LOW (case cold). Generated date: 2026.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-009_CIVIX_P0019_AbsconderStatus_2026.pdf

#### EVD-007-010 — Police Sketch (P0019 Shyam Meena)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Police composite sketch of P0019 (Shyam Meena) created from victim and witness descriptions. Key features: angular face, thin moustache, scar above left eyebrow. Sketch circulated to Rajasthan Police and border check posts. Retained in case file for potential future identification match.
- **Associated Persons:** P0019 (Shyam Meena)
- **Associated Organizations:** Uttam Nagar PS Forensic Artist
- **Prompt for Antigravity:** Generate: Police composite sketch (pencil-drawn style). Male face: angular features, thin moustache, visible scar above left eyebrow, estimated age 30-35 (as of 2013). "WANTED" header. Police case reference number, description text below sketch. Police station stamp.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-010_Police_Sketch_P0019_ShyamMeena.png

#### EVD-007-011 — Arms Recovery (From Arrested Suspects)
- **Type:** BALLISTICS_REPORT
- **Description:** Arms seizure and ballistics report for one country-made pistol recovered from P0018 at time of arrest. Pistol: .32 bore, hand-crafted, serial filed. CFSL test: functional. Rifling pattern: consistent with Munger district Bihar origin (similar to CIVIX-006 weapons — establishing possible same supply network).
- **Associated Persons:** P0018 (Ramkishan Bairwa — arrested with weapon)
- **Associated Organizations:** CFSL, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Arms seizure and CFSL ballistics report. Include: weapon recovered from P0018 (date of arrest), description (.32 bore country-made), serial filed, functional test result, rifling comparison note (Bihar-origin pattern, similar to Munger district manufacture), CFSL examiner note re: possible common supply with other cases.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-011_Ballistics_P0018_Pistol_Bihar_Munger_Pattern.pdf

#### EVD-007-012 — Bank Account Analysis (Advance Money)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Analysis of P0018's bank account (Jan Dhan account, Uttam Nagar branch) showing two large cash deposits of ₹25,000 and ₹30,000 in December 2012 and January 2013 — immediately before the crime series. P0018's claimed income (daily wage labor, ~₹500/day) cannot explain these deposits. Consistent with P0018's testimony about "advance money from Suresh Ji."
- **Associated Persons:** P0018 (Ramkishan Bairwa), P0307 ("Suresh Ji" — source of funds)
- **Associated Organizations:** Bank (Jan Dhan account), Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Bank account statement analysis (financial investigation format). Include: account details (Jan Dhan, P0018's name), transaction history (Nov 2012–Jan 2013), two suspicious cash deposits (₹25,000 on 2012-12-15, ₹30,000 on 2013-01-05), comparison to declared income, investigator's annotation highlighting deposits.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-012_Bank_Statement_P0018_AdvanceMoney_Deposits.pdf

#### EVD-007-013 — Magistrate Remand Orders
- **Type:** COURT_ORDER
- **Description:** Series of police custody remand orders for P0018 during investigation. Three 2-day remands (total 6 days police custody). Remand application specifies: need to interrogate about "Delhi contact," recover stolen property, and cross-examine with co-accused. Court granted all three remands.
- **Associated Persons:** P0018 (Ramkishan Bairwa)
- **Associated Organizations:** Metropolitan Magistrate Court, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: Three police custody remand orders (one document, consecutive remands). Each: case number, accused name, grounds (investigation of Delhi contact, property recovery, co-accused confrontation), period (2 days each), magistrate signature, date of each order (Jan 2013).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-007-013_Remand_Orders_P0018_3x2Days.pdf

#### EVD-007-014 — CIVIX Cross-Case IC-003 Analysis
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX detailed analysis of IC-003 ("Suresh Ji" = possibly P0001 Suresh Valmiki). Generated in 2026 after P0001's arrest in CIVIX-009. Analysis compares: P0018's 2013 testimony description of "Suresh Ji" against P0001's confirmed profile. Match factors: name, Delhi base, N1 network role, advance-money facilitation. Score updated to 0.61 (MODERATE) post-P0001 arrest. Flagged for investigator action.
- **Associated Persons:** P0307 ("Suresh Ji"), P0001 (Suresh Valmiki)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: CIVIX IC-003 detailed analysis report. Compare P0307 vs P0001. Previous score: 0.41 (2013 data). Updated score: 0.61 (2026, post-P0001 arrest). Confidence increase basis: P0001 confirmed N1 network role. Recommendation: "Confront P0001 with P0018's 2013 testimony during interrogation. Request P0018 (released 2018) be recalled as witness."
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-014_CIVIX_IC003_Updated_SureshJi_P0001_2026.pdf

#### EVD-007-015 — CIVIX Cold Case Reactivation Assessment
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX automated assessment of CIVIX-007 reactivation potential following P0001's 2026 arrest. Assessment: P0018 released from prison 2018 and available as witness; P0019 still absconding; IC-003 updated to 0.61. Recommendation: Reactivate case to REOPENED, recall P0018, confront P0001 with "Suresh Ji" testimony, issue fresh lookout for P0019. Score: 0.61.
- **Associated Persons:** P0018, P0019, P0307, P0001
- **Associated Organizations:** CIVIX System, Uttam Nagar PS
- **Prompt for Antigravity:** Generate: CIVIX cold case reactivation report for CIVIX-007. Include: case age (13 years cold), new trigger (P0001 arrest CIVIX-009), IC-003 update, available witnesses (P0018 released 2018), recommendation (REOPEN, recall P0018, confront P0001). Score 0.61, Priority: MEDIUM.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-007-015_CIVIX_ColdCase_Reactivation_CIVIX007_2026.pdf

---

### CIVIX-008: Jewellery Heist — DLF Phase 1 Showroom (2023)
**Status:** ACTIVE | **Area:** Gurugram PS | **Suspects:** P0020, P0021, P0022
**Network:** N1 | **Opened:** 2023-03-18

#### EVD-008-001 — CCTV Stills (Tanishq Showroom, 4 Frames)
- **Type:** CCTV_CLIP
- **Description:** Four still frames extracted from Tanishq showroom CCTV (2023-era, 720p). Frame 1: Three suspects entering showroom (2023-03-18 14:17). Frame 2: P0022 (female) engaging staff in conversation (14:19). Frame 3: Two male suspects at display case, one attempting to open (14:21). Frame 4: All three at exit, suspected jewelry in bag (14:22). Faces: P0020 partially visible (cap, glasses), P0021 and P0022 more clearly visible.
- **Associated Persons:** P0020 (Birju Jaat), P0021 (Sunil Gujjar), P0022 (Sonia Kumari)
- **Associated Organizations:** Tanishq DLF Phase 1, Gurugram PS
- **Prompt for Antigravity:** Generate: Four CCTV stills (720p, 2023 quality, full color). Scene: jewelry showroom interior. Frame 1: three persons entering (man-woman-man formation). Frame 2: woman chatting with sales staff, smiling. Frame 3: two men at display case, suspicious posture. Frame 4: three at exit, one carrying bag. Timestamp: 14:17, 14:19, 14:21, 14:22. Showroom camera ID overlay.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-008-001_CCTV_Tanishq_DLF_4Frames_2023-03-18.jpg

#### EVD-008-002 — FIR (No. 189/2023, Gurugram PS)
- **Type:** FIR_PDF
- **Description:** FIR No. 189/2023 filed at Gurugram PS for jewelry theft from Tanishq showroom, DLF Phase 1, on 2023-03-18. Stolen: jewelry valued at ₹42 lakh. Three suspects: P0020 (Birju Jaat — identified by witness P0308), P0021 (Sunil Gujjar — absconding), P0022 (Sonia Kumari — absconding). Suspects fled in Hyundai Creta HR-07AZ-0999 (subsequently found abandoned).
- **Associated Persons:** P0020 (Birju Jaat), P0021, P0022
- **Associated Organizations:** Gurugram PS, Tanishq (TATA brand)
- **Prompt for Antigravity:** Generate: Gurugram PS FIR No. 189/2023. Date: 2023-03-18. Include: Tanishq DLF Phase 1 location, 3 suspects (named), jewelry stolen (₹42 lakh estimate), escape vehicle (Hyundai Creta HR-07AZ-0999), found abandoned (DLF Phase 3 parking), witness reference (P0308 — former Tanishq employee identifying P0020 by distinctive walk).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-002_FIR_Gurugram_PS_189_2023_Tanishq.pdf

#### EVD-008-003 — Witness Statement (P0308 — Walk Identification)
- **Type:** WITNESS_STATEMENT
- **Description:** Statement from P0308 (Anita Verma, former Tanishq employee). She recognizes P0020 (Birju Jaat) from his distinctive gait: "He has a slight rolling walk on his left side, from an old knee injury. I worked with him for 8 months at another jewelry showroom 3 years ago and would recognize his walk anywhere." This is the sole identification evidence for P0020. Evidence is unique and potentially decisive.
- **Associated Persons:** P0308 (Anita Verma, witness), P0020 (Birju Jaat — identified)
- **Associated Organizations:** Gurugram PS
- **Prompt for Antigravity:** Generate: Witness statement (police format). Witness: Anita Verma, former jewelry showroom employee. Q&A: "How do you identify the suspect?" — "He has a distinctive rolling walk on his left side, old knee injury. I worked with him at [showroom name] for 8 months. I am 100% certain." Signature, date (2023-03-19), Gurugram PS stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-003_Witness_Statement_P0308_WalkIdentification.pdf

#### EVD-008-004 — Vehicle Recovery Report (Abandoned Creta)
- **Type:** VEHICLE_SEIZURE
- **Description:** Recovery report for Hyundai Creta HR-07AZ-0999 found abandoned in DLF Phase 3 parking lot at 16:45 on 2023-03-18 (2.5 hours after heist). Vehicle was stolen 3 days prior from Faridabad. No jewelry found in vehicle. Fingerprints collected from steering wheel, door handle, and gear shift. Partial prints sent to AFIS — no match in 2023 database.
- **Associated Persons:** P0020, P0021, P0022 (occupants), original Faridabad owner (VICTIM)
- **Associated Organizations:** Gurugram PS, Faridabad PS (original theft)
- **Prompt for Antigravity:** Generate: Vehicle recovery report (police form). Include: vehicle (Hyundai Creta HR-07AZ-0999, white), location found (DLF Phase 3, parking lot C), time (16:45, 2023-03-18), original theft FIR reference (Faridabad), fingerprint collection status (collected, sent AFIS), interior search result (no jewelry), seizing officer, Gurugram PS stamp.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-004_Vehicle_Recovery_Creta_HR-07AZ-0999_DLF.pdf

#### EVD-008-005 — Tanishq Inventory (Stolen Jewelry)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Tanishq's official inventory of stolen items: 14 gold necklaces (various designs, 22K, total 180 grams), 6 diamond earring pairs (certified, total 3.2 carats), 2 platinum bangles, 8 gold rings. Total insured value: ₹42,00,000. Inventory certified by store manager and submitted to Gurugram PS and insurance company.
- **Associated Persons:** Tanishq store manager (fictional)
- **Associated Organizations:** Tanishq (TATA), insurance company
- **Prompt for Antigravity:** Generate: Retail inventory loss report (Tanishq letterhead). Include: itemized jewelry inventory (categories, weights, carats, per-item values), total: ₹42,00,000. Certified by store manager signature. TATA/Tanishq logo. Date: 2023-03-18. "This document is submitted to Gurugram PS and [Insurance Company] for claim purposes."
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-005_Tanishq_Inventory_Stolen_42L_2023.pdf

#### EVD-008-006 — ANPR Log (Creta HR-07AZ-0999)
- **Type:** ANPR_CROP
- **Description:** ANPR log showing Hyundai Creta HR-07AZ-0999 on 2023-03-18. Three entries: (1) CAM at Gurugram Sector 44 (EVENT-040, 14:07 — approaching from Sector 44 toward DLF Phase 1, 15 minutes before theft). (2) DLF Phase 1 parking camera (14:16). (3) DLF Phase 3 exit camera (16:42, 3 minutes before recovery). This ANPR trail reconstructs the suspects' complete movement.
- **Associated Persons:** P0020, P0021, P0022 (occupants of vehicle)
- **Associated Organizations:** Gurugram Traffic Police, Gurugram PS
- **Prompt for Antigravity:** Generate: ANPR log extract (table format). Three rows: (1) Timestamp 14:07, Camera GGN-SEC44-ANPR, Plate HR-07AZ-0999, Direction "toward DLF Phase 1." (2) Timestamp 14:16, DLF-P1-PARKING-CAM, same plate, "entering parking." (3) Timestamp 16:42, DLF-P3-EXIT, same plate, "exiting." Timeline reconstructed below table.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-008-006_ANPR_Creta_HR-07AZ-0999_Timeline_2023.pdf

#### EVD-008-007 — P0020 Arrest Memo
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Arrest memo for P0020 (Birju Jaat), arrested based on witness identification by P0308. Arrest date: 2023-03-21 (3 days post-heist), location: P0020's residence in Gurugram Sector 9. Items seized at arrest: ₹15,000 cash (unaccounted), two mobile phones, one new gold chain (not matching stolen inventory — possibly from prior crime).
- **Associated Persons:** P0020 (Birju Jaat)
- **Associated Organizations:** Gurugram PS
- **Prompt for Antigravity:** Generate: Arrest memo (police format). Include: accused (Birju Jaat, P0020), date/time of arrest (2023-03-21), location (Sector 9 Gurugram), arresting officer, grounds (witness identification by P0308), items seized (₹15,000 cash, 2 phones, 1 gold chain), court produced date, charges.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-007_Arrest_Memo_P0020_BirjuJaat_2023-03-21.pdf

#### EVD-008-008 — P0020 Interrogation Transcript
- **Type:** INTERROGATION_TRANSCRIPT
- **Description:** Interrogation transcript of P0020 (Birju Jaat). P0020 denies involvement: "I was not at DLF Phase 1 that day. Anita Verma has a personal grudge against me." However, CDR places his phone near DLF Phase 1 at 14:00–15:00. P0020 later admits "I may have driven near that area" but denies entering the showroom. Partial admission recorded.
- **Associated Persons:** P0020 (Birju Jaat), investigating officer
- **Associated Organizations:** Gurugram PS
- **Prompt for Antigravity:** Generate: Interrogation transcript (typed, police format). Q&A format. Initial denial → confronted with CDR evidence → "I may have been near there." Note: P0020 claims Anita Verma has personal motive for false identification. IO observation: "Suspect's manner became visibly uncomfortable when presented with CDR printout." Date: 2023-03-22.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-008_Interrogation_P0020_BirjuJaat_PartialAdmission.pdf

#### EVD-008-009 — CDR (P0020 Phone, DLF Phase 1 Tower)
- **Type:** CDR_DUMP
- **Description:** CDR extract for P0020's primary phone showing tower pings to TOWER-GGN-DLF01 (covering DLF Phase 1 area) from 13:50 to 15:15 on 2023-03-18. Phone switched off at 15:15 (shortly after theft confirmed). Reactivated 17:00 in Sohna Road area. Pattern consistent with deliberate mobile discipline during crime.
- **Associated Persons:** P0020 (Birju Jaat)
- **Associated Organizations:** Jio (telecom), Gurugram PS
- **Prompt for Antigravity:** Generate: CDR extract (CSV format). Date: 2023-03-18. Show: 13:50-15:15 pings to TOWER-GGN-DLF01, call events during this window, 15:15 — phone switches off, 17:00 — phone reactivates at TOWER-GGN-SOHNA02. Include column: [Timestamp, Event_Type, Tower_ID, Tower_Location, Duration].
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-008-009_CDR_P0020_DLF_Tower_2023-03-18.csv

#### EVD-008-010 — Lookout Circulars (P0021, P0022)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Joint lookout circular for P0021 (Sunil Gujjar) and P0022 (Sonia Kumari), both absconding after the DLF Phase 1 heist. CCTV stills from Tanishq used as photo reference. Circulated to NCR, Rajasthan, and UP border points. P0022's unusual prominence (female accomplice using distraction technique) noted as distinguishing MO.
- **Associated Persons:** P0021 (Sunil Gujjar), P0022 (Sonia Kumari)
- **Associated Organizations:** Gurugram PS, Delhi Police, Rajasthan/UP border police
- **Prompt for Antigravity:** Generate: Joint lookout circular for two suspects. P0021: male, ~30, medium build. P0022: female, ~25-28, noted MO (distraction technique, jewelry theft). CCTV image references attached (described, not actual photos). Reward if applicable. Contact: Gurugram PS.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-010_Lookout_P0021_P0022_Gurugram_DLF.pdf

#### EVD-008-011 — Faridabad Vehicle Theft FIR (Stolen Creta)
- **Type:** FIR_PDF
- **Description:** FIR from Faridabad PS for the theft of Hyundai Creta HR-07AZ-0999, filed 2023-03-15 (3 days before the jewelry heist). Vehicle theft MO: stolen from residential parking at night. Original owner confirmed vehicle stolen 2023-03-15. This establishes the Creta as a stolen vehicle used as a tool for the heist — a common MO in this network.
- **Associated Persons:** Original owner (victim, fictional), P0020 (or accomplice — suspected thief of Creta)
- **Associated Organizations:** Faridabad PS, Gurugram PS
- **Prompt for Antigravity:** Generate: Faridabad PS FIR (vehicle theft). Date: 2023-03-15. Vehicle: Hyundai Creta HR-07AZ-0999, white. Complainant: original owner (fictional name). Location stolen: residential parking, Faridabad. Time last seen and when discovered missing. FIR number, IO name.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-011_FIR_Faridabad_Creta_Theft_2023-03-15.pdf

#### EVD-008-012 — Chargesheet (P0020)
- **Type:** COURT_ORDER
- **Description:** Chargesheet filed against P0020 (Birju Jaat) for the Tanishq DLF heist. Charges: IPC 392 (robbery), 411 (dishonestly receiving stolen property — re: gold chain found at arrest), 34 (common intention). Evidence: CCTV stills (EVD-008-001), witness identification (EVD-008-003), CDR (EVD-008-009). P0021 and P0022 listed as absconding co-accused.
- **Associated Persons:** P0020 (chargesheeted), P0021, P0022 (absconding co-accused)
- **Associated Organizations:** Gurugram PS, Gurugram Sessions Court
- **Prompt for Antigravity:** Generate: Chargesheet document (police format). Accused: P0020 (Birju Jaat). Charges: IPC 392, 411, 34. Evidence summary: CCTV (4 frames), witness identification (P0308, walk), CDR (DLF Phase 1 tower, 13:50–15:15). Co-accused at large listed with NBW status. IO certification, date of filing (2023-04-15).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-012_Chargesheet_P0020_BirjuJaat_Tanishq.pdf

#### EVD-008-013 — Tanishq Insurance Claim (₹42 Lakh)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Tanishq/TATA insurance claim for stolen jewelry (₹42 lakh). Insured under retail theft policy. Insurance assessor visited store 2023-03-20, verified inventory loss. Claim filed 2023-03-25. Insurance company investigator's note: "CCTV footage reviewed; theft confirmed as planned professional operation." Claim approved for ₹36.4 lakh (86.7%), with holdback pending conviction.
- **Associated Persons:** Tanishq store manager
- **Associated Organizations:** Tanishq (TATA), Insurance Company
- **Prompt for Antigravity:** Generate: Insurance claim and assessment report. Include: claim number, insured (Tanishq DLF Phase 1), amount (₹42,00,000), assessor visit note, approved amount (₹36,40,000 — 86.7%), holdback explanation (pending conviction), date.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-008-013_Insurance_Claim_Tanishq_42L_86pct_Approved.pdf

#### EVD-008-014 — Cross-Case Link (P0020 and CIVIX-003 Associate)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX entity relationship note establishing that P0020 (Birju Jaat) has a known prior associate connection with Manjeet Rawat (who appears in CIVIX-003). The connection was established via a 2021 police record in Rajasthan where both P0020 and a person matching Manjeet Rawat's description were detained (not arrested) for suspicious behavior at a highway dhaba.
- **Associated Persons:** P0020 (Birju Jaat), Manjeet Rawat (CIVIX-003 connected)
- **Associated Organizations:** CIVIX System, Rajasthan Police
- **Prompt for Antigravity:** Generate: CIVIX entity link report. Relationship: P0020 ↔ Manjeet Rawat. Evidence: 2021 Rajasthan Police detention record (both present at highway dhaba, same incident). Relationship type: KNOWN_ASSOCIATE (unconfirmed criminal conspiracy). Confidence: 0.38 (LOW). Cross-case: CIVIX-003, CIVIX-008.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-008-014_CIVIX_CrossCase_P0020_ManjeetRawat_CIVIX003.pdf

#### EVD-008-015 — CIVIX Investigative Lead (P0021 P0022 Whereabouts)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX lead (LEAD-008-A) generated for locating absconding P0021 and P0022. CDR analysis shows P0021's last known phone activity was in Sohna (Haryana) on 2023-03-20. P0022's last ping: Faridabad, 2023-03-19. Both phones have been off since. CIVIX recommends: alert Sohna PS for P0021, Faridabad network monitoring for P0022. Score: 0.59.
- **Associated Persons:** P0021 (Sunil Gujjar), P0022 (Sonia Kumari)
- **Associated Organizations:** CIVIX System, Gurugram PS
- **Prompt for Antigravity:** Generate: CIVIX lead report LEAD-008-A. Content: P0021 last CDR ping (Sohna, 2023-03-20), P0022 last CDR ping (Faridabad, 2023-03-19). Both phones dark since then. Recommendations: Sohna PS alert (P0021), Faridabad surveillance (P0022), check Haryana border crossings. Score 0.59, Priority MEDIUM.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-008-015_CIVIX_Lead_LEAD008A_P0021_P0022_Whereabouts.pdf

---

### CIVIX-009: Najafgarh Cash-in-Transit Robbery — Suresh Valmiki Apprehended (2026) [HERO-04]
**Status:** ACTIVE | **Area:** Najafgarh PS | **Suspects:** P0001, P0023, P0024
**Network:** N1 | **Opened:** 2026-07-19

#### EVD-009-001 — AFIS Booking Card (P0001 Ten Prints)
- **Type:** AFIS_FINGERPRINT
- **Description:** Ten-print fingerprint card for P0001 (Suresh Valmiki) taken immediately after arrest at Najafgarh PS on 2026-07-19 at 11:30 (EVENT-052). Both hands: rolled prints of all 10 digits, plain prints, palm prints. Card pushed to AFIS system at 11:45. Within 4 hours (EVENT-052+), AFIS returned the match to LATENT-2021-NH48-001 from CIVIX-003 at 93% confidence. This card is the triggering evidence for LEAD-004.
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** Najafgarh PS, AFIS Bureau
- **Prompt for Antigravity:** Generate: 10-print fingerprint card. Include: suspect name (Suresh Valmiki, P0001), DOB, arrest date (2026-07-19), case reference (FIR 441/2026 Najafgarh PS), rolled prints (10 digits, both hands), plain prints, palm prints, certifying constable signature, date. Note at bottom: "Submitted to AFIS: 11:45 hrs. Match returned: 15:23 hrs (LATENT-2021-NH48-001, 93%)."
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-001_AFIS_10Print_P0001_SureshValmiki_2026.png

#### EVD-009-002 — AFIS Match Result Report
- **Type:** AFIS_FINGERPRINT
- **Description:** AFIS system match result report for P0001 (Suresh Valmiki). Confirms: Right thumb print from booking card matches latent print LATENT-2021-NH48-001 (lifted from NH-48 cash van steering wheel, CIVIX-003) at 93.1% confidence (7 of 7 ridge characteristics match, partial print quality adjusted). This is the HERO-04 discovery chain's central forensic event. LEAD-004 auto-generated at 15:47 hrs.
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** AFIS Bureau, Najafgarh PS, CIVIX System
- **Prompt for Antigravity:** Generate: AFIS match report (system output format). Include: query print (P0001 right thumb, booking 2026-07-19), matched latent (LATENT-2021-NH48-001, case CIVIX-003, date lifted 2021-11-05), confidence score (93.1%), ridge characteristics matched (7 of 7 visible), verification by forensic examiner, CIVIX lead generated flag (LEAD-004, timestamp 15:47).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-002_AFIS_Match_P0001_vs_LATENT_2021_NH48_93pct.pdf

#### EVD-009-003 — CCTV Still (CAM-04, P0001 at Bus Terminal)
- **Type:** CCTV_CLIP
- **Description:** CCTV still from CAM-04 (Najafgarh Bus Terminal camera) showing P0001 (Suresh Valmiki) in clear view at 2026-07-19 08:55 — the exact time of the robbery (EVENT-050). P0001 visible at the robbery location, partially masked, approaching the PNB cash van. This is direct physical placement evidence. Image quality: 1080p (modern camera, 2026-era).
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** Najafgarh PS, Delhi Transport Authority (CCTV operator)
- **Prompt for Antigravity:** Generate: 2026-era 1080p CCTV still (color, sharp). Scene: bus terminal forecourt, daylight. Individual matching P0001's description (male, ~35, dark complexion, black jacket, partial face mask): approaching a white cash van. Include: timestamp overlay (2026-07-19 08:55:23), camera ID (CAM-04), GPS coordinates, bus terminal background.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-003_CCTV_CAM04_P0001_BusTerminal_2026-07-19.jpg

#### EVD-009-004 — FIR (No. 441/2026, Najafgarh PS)
- **Type:** FIR_PDF
- **Description:** FIR No. 441/2026 filed at Najafgarh PS for armed robbery of PNB cash van at Najafgarh Bus Terminal. ₹58 lakh seized. Four suspects. One arrested on-scene (P0001 Suresh Valmiki, apprehended at Najafgarh Railway Crossing). Three escaped (P0023, P0024, and one unidentified). Guard P0309 (Rajveer Singh) assaulted. P0001 booked immediately.
- **Associated Persons:** P0001 (arrested), P0023, P0024 (absconding), P0309 (victim guard)
- **Associated Organizations:** Najafgarh PS, PNB Bank
- **Prompt for Antigravity:** Generate: Najafgarh PS FIR No. 441/2026. Date/time: 2026-07-19 08:55. Include: PNB cash van robbery, ₹58 lakh, four suspects, P0001 arrested at Railway Crossing at 09:14, three escaped, guard P0309 assaulted (lathi blow, shoulder injury), case registered, standard intake ordered (ten-print, medical exam, remand).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-004_FIR_Najafgarh_PS_441_2026_CashVan.pdf

#### EVD-009-005 — CDR (T0011 at TOWER-NJ-01)
- **Type:** CDR_DUMP
- **Description:** CDR extract for T0011 (P0001's registered SIM) showing device ping to TOWER-NJ-01 (Najafgarh Railway Crossing area) at 08:51:07 on 2026-07-19 — 4 minutes before the robbery (EVENT-053). Phone switched off 08:54 (1 minute before robbery). This CDR establishes P0001's confirmed presence at the crime location. Cross-referenced: same T0011 pings TOWER-RH-01 in CIVIX-027 (the hero chain link).
- **Associated Persons:** P0001 (Suresh Valmiki — T0011 owner)
- **Associated Organizations:** Airtel, Najafgarh PS
- **Prompt for Antigravity:** Generate: CDR extract (CSV, 2026-07-19). Key rows: 08:51:07 — T0011 pings TOWER-NJ-01 (Najafgarh Railway Crossing), call type (idle registration/data), 08:54 — phone goes offline. Include surrounding context (08:00–09:30 window). Tower location descriptions. Annotated note: "Phone last active 4 minutes before robbery, at robbery location."
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-005_CDR_T0011_TOWER-NJ-01_2026-07-19.csv

#### EVD-009-006 — P0001 Arrest and Medical Exam
- **Type:** MEDICAL_REPORT
- **Description:** Arrest memo and mandatory medical examination for P0001 (Suresh Valmiki) conducted at Najafgarh PS after arrest. Examination (2026-07-19 13:00): no injuries requiring hospitalization. Notation: "Old scar tissue on left knee consistent with prior fracture." Physical profile: age ~35, height 5'10", weight 78 kg, identifying marks (lotus tattoo right forearm — matching witness descriptions from CIVIX-001 and CIVIX-003).
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** Najafgarh Government Hospital, Najafgarh PS
- **Prompt for Antigravity:** Generate: Arrest medical examination report. Include: suspect (Suresh Valmiki), date (2026-07-19), physician, physical measurements, identifying marks (CRITICAL: "Lotus flower tattoo, right forearm, approximately 3 cm diameter, appears professionally inked"), old knee scar, GSR negative (arrested after escape attempt), conclusion (fit for custody).
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-006_Arrest_Medical_P0001_LotusTattoo_2026.pdf

#### EVD-009-007 — PNB Bank Loss Report
- **Type:** FINANCIAL_STATEMENT
- **Description:** PNB Bank formal loss report for the 2026-07-19 Najafgarh robbery. ₹58 lakh in cash (mixed denomination: ₹500 and ₹2000 notes, serials recorded). Cash was in transit to Najafgarh branch for ATM replenishment. Insurance claim filed immediately. Bank confirms the robbery was timed to coincide with peak ATM replenishment schedule.
- **Associated Persons:** PNB branch manager (fictional), P0309 (guard victim)
- **Associated Organizations:** PNB Bank, Najafgarh Branch, Insurance Company
- **Prompt for Antigravity:** Generate: PNB Bank internal loss report. Include: amount (₹58,00,000), denomination breakdown (₹500 × 60,000 notes + ₹2000 × 10,000 notes), serial number range (redacted for security — note "recorded internally"), cash van details, guard injury reference, insurance claim number, date.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-007_PNB_Bank_Loss_Report_58L_2026.pdf

#### EVD-009-008 — P0309 Guard Statement (Rajveer Singh)
- **Type:** WITNESS_STATEMENT
- **Description:** Statement from P0309 (Rajveer Singh, PNB guard) taken at hospital on 2026-07-19 after treatment for shoulder injury (lathi blow). Rajveer describes: "Four men in masks. One man (later identified as the arrested suspect) had a distinctive lotus tattoo on his right arm — his sleeve was pushed up as he struck me." This tattoo identification independently corroborates P0308 (CIVIX-008) and toll operator (CIVIX-003).
- **Associated Persons:** P0309 (Rajveer Singh, victim), P0001 (suspect identified)
- **Associated Organizations:** Najafgarh PS, PNB Bank
- **Prompt for Antigravity:** Generate: Witness statement (police format, recorded at hospital bedside). Witness: Rajveer Singh, guard, PNB. "The man who hit me — his sleeve rode up. He had a lotus flower tattooed on his right arm. I am certain of this." Full Q&A format. Witness signed from hospital bed (signature shaky, noted). Date: 2026-07-19.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-008_Statement_P0309_RajveerSingh_LotusTattoo.pdf

#### EVD-009-009 — LEAD-004 Auto-Generated Report (AFIS Chain)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX auto-generated LEAD-004 report (the central HERO-04 discovery). Generated at 15:47 on 2026-07-19, 4 hours after P0001's AFIS booking. Content: AFIS match (EVD-009-002), cross-case identification (P0001 = CIVIX-003 latent print suspect), recommendation (reopen CIVIX-003 immediately, reclassify P0001's role from "NH-48 robbery accused" to "3-case serial offender"), confidence 0.93.
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** CIVIX System, Najafgarh PS
- **Prompt for Antigravity:** Generate: CIVIX LEAD-004 full report. Lead ID: LEAD-004. Generated: 2026-07-19 15:47:33. Trigger: AFIS match. Content: "Subject P0001 (Suresh Valmiki) arrested CIVIX-009 matches latent print LATENT-2021-NH48-001 (CIVIX-003) at 93% confidence. Recommend: (1) REOPEN CIVIX-003 immediately. (2) P0001 is now suspect in 3 robbery cases: CIVIX-001 (alias match), CIVIX-003 (fingerprint), CIVIX-009 (arrested). (3) Alert Dwarka PS re CIVIX-001 alias chain." Priority: CRITICAL.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-009_CIVIX_LEAD004_AFIS_Chain_P0001_3Cases.pdf

#### EVD-009-010 — Lookout Notice (P0023, P0024)
- **Type:** INTELLIGENCE_REPORT
- **Description:** Immediate lookout circular for P0023 and P0024 (escaped suspects from 2026-07-19 robbery). Based on CAM-04 CCTV: P0023 described as tall male (6'1"+), thin build, wearing blue tracksuit. P0024: shorter, stocky, red hoodie. Circulated within 2 hours of robbery. NCR, Haryana, Rajasthan border check posts alerted.
- **Associated Persons:** P0023, P0024
- **Associated Organizations:** Najafgarh PS, Delhi Police HQ
- **Prompt for Antigravity:** Generate: Emergency lookout circular (same-day issuance, 2026-07-19). Two suspects: P0023 (tall, thin, blue tracksuit) and P0024 (shorter, stocky, red hoodie). CCTV reference attached (described). Immediate alert level. Reward if any. Contact: Najafgarh PS SHO, phone number.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-010_Lookout_P0023_P0024_Emergency_2026.pdf

#### EVD-009-011 — Remand Application (P0001)
- **Type:** COURT_ORDER
- **Description:** Police custody remand application for P0001 (Suresh Valmiki). Grounds: investigation of three linked robbery cases (CIVIX-003, CIVIX-009, CIVIX-001 alias chain), recovery of ₹58 lakh in stolen cash, identification of two escaped co-accused, questioning about N1 network leadership. Court granted 5 days police custody.
- **Associated Persons:** P0001 (Suresh Valmiki)
- **Associated Organizations:** Najafgarh PS, Metropolitan Magistrate
- **Prompt for Antigravity:** Generate: Police custody remand application and court order. Application: grounds listed (3 cases, cash recovery, co-accused identification). Court order: GRANTED, 5 days police custody, date range, magistrate signature and seal. Next remand date.
- **Source Preference:** GENERATE_FORENSIC_MOCKUP
- **Output Filename:** EVD-009-011_Remand_P0001_5Days_Granted_2026.pdf

#### EVD-009-012 — Tattoo Identification Cross-Reference
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX entity cross-reference document showing the lotus tattoo identification appearing independently in three separate cases: (1) CIVIX-001 — Rajesh Kumar witness statement (2012), (2) CIVIX-003 — toll plaza operator witness statement (2021), (3) CIVIX-009 — guard Rajveer Singh statement (2026). All three independently describe "lotus flower, right forearm." This convergence of independent witness identification is presented as corroborating evidence.
- **Associated Persons:** P0001 (Suresh Valmiki — tattoo bearer)
- **Associated Organizations:** CIVIX System
- **Prompt for Antigravity:** Generate: CIVIX multi-source corroboration report. Title: "Tattoo Identification: Independent Convergence." Three evidence items in a table: Case / Witness / Year / Description. All three: "lotus flower, right forearm." Conclusion: "Three independent witnesses across 14 years describe the same identifying mark on P0001. Corroboration confidence: 0.91." System timestamp.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-012_CIVIX_Tattoo_Crossref_P0001_3Cases.pdf

#### EVD-009-013 — P0001 Criminal History Extract
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX-compiled criminal history for P0001 (Suresh Valmiki) as of 2026-07-19 (day of arrest). History: (1) 2012 CIVIX-001 — alias "Vikram @ Pandit" (PERSON_UNKNOWN_05); (2) 2021 CIVIX-003 — latent print LATENT-2021-NH48-001 (unidentified until 2026); (3) 2026 CIVIX-009 — arrested with alias "Suri Bhai." Three separate case identities now merged into single entity P0001.
- **Associated Persons:** P0001 (Suresh Valmiki / "Vikram @ Pandit" / "Suri Bhai")
- **Associated Organizations:** CIVIX System, Najafgarh PS
- **Prompt for Antigravity:** Generate: CIVIX criminal history card (comprehensive). Subject: Suresh Valmiki (P0001). Aliases: "Vikram @ Pandit" (2012 usage), "Suri Bhai" (2026 usage). Three-row crime history table: 2012 (CIVIX-001, alias match), 2021 (CIVIX-003, latent print), 2026 (CIVIX-009, arrested). Network: N1 Armed Robbery. XGBoost Score: 0.92 (CRITICAL).
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-013_CIVIX_CriminalHistory_P0001_ThreeCases.pdf

#### EVD-009-014 — Property Valuation (Yadav Properties — Financial Trace Initiation)
- **Type:** FINANCIAL_STATEMENT
- **Description:** Document initiating financial trace from P0001's (Suresh Valmiki's) robbery proceeds to Dinesh Yadav (P0120) and Yadav Properties (CIVIX-044). CIVIX flags: Dinesh Yadav is P0001's brother. Post-2021 robbery (CIVIX-003), ₹58 lakh disappeared. Yadav Properties registered a 4.2-acre land parcel in Gurugram in 2022-03-15 for ₹58 lakh cash (CIVIX-044). Temporal and amount match: 97% correlation.
- **Associated Persons:** P0001, P0120 (Dinesh Yadav — brother)
- **Associated Organizations:** CIVIX System, Yadav Properties Pvt Ltd (ORG-001)
- **Prompt for Antigravity:** Generate: CIVIX financial trace initiation report. Source event: ₹58L robbery proceeds (CIVIX-003, 2021-11-05). Trace: proceeds → P0001 → P0120 (brother, Dinesh Yadav) → Yadav Properties → Khasra 447 Gurugram Sec 44 (₹58L cash, 2022-03-15). Amount correlation: 100%. Temporal gap: 87 days. LEAD-005 generated. Cross-case: CIVIX-044.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-014_CIVIX_Financial_Trace_P0001_Proceeds_CIVIX044.pdf

#### EVD-009-015 — CIVIX Hero Case Summary (HERO-04 Three-Hop Chain)
- **Type:** INTELLIGENCE_REPORT
- **Description:** CIVIX comprehensive summary of the HERO-04 discovery chain. Three-hop path: (1) P0001 arrested CIVIX-009 → (2) AFIS match → CIVIX-003 reopened (LEAD-004) → (3) Financial trace → CIVIX-044 (robbery proceeds → Dinesh Yadav's benami land). Chain demonstrates CIVIX's core capability: connecting a routine arrest (hop 1) to a cold case (hop 2) to hidden asset recovery (hop 3) — all within 24 hours of arrest.
- **Associated Persons:** P0001, P0120
- **Associated Organizations:** CIVIX System, Najafgarh PS, Gurugram PS
- **Prompt for Antigravity:** Generate: CIVIX HERO-04 discovery chain summary card. Title: "Three-Hop Discovery: CIVIX-009 → CIVIX-003 → CIVIX-044." Timeline: Hour 0 — P0001 arrested; Hour 4 — AFIS triggers LEAD-004 (CIVIX-003 reopen); Hour 6 — financial trace generates LEAD-005 (CIVIX-044 Yadav Properties); Hour 24 — Gurugram PS opens investigation. Capability demonstrated: AFIS + Financial Trace + Cross-Case Link. This is the hero demo centerpiece.
- **Source Preference:** GENERATE_SYNTHETIC
- **Output Filename:** EVD-009-015_CIVIX_HERO04_ThreeHop_Discovery_Summary.pdf

---

# CIVIX 2.0 — UNIVERSE BIBLE PART 2
## Complete 55-Case Deep Specification Matrix

Every case below specifies: FIR narrative, suspects with roles, key events, evidence artifacts, hypotheses, cross-case relationships, investigator discovery targets, and CIVIX capability tags.

---

# NETWORK N1 — ARMED ROBBERY & CASH-IN-TRANSIT SYNDICATE (Cases 001–009)

---

## CIVIX-001 | "The Fifth Robber" — Dwarka Sector 23 (2012) [HERO-01]
**Status:** CLOSED_SOLVED (partial) | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Dwarka PS | **Opened:** 2012-03-14 | **Lead Investigator:** IO Bhim Singh (U001)

**FIR Narrative:** At 07:43 on 14 March 2012, five masked persons intercepted an SBI cash van at the Dwarka Sector 23 T-junction. Three security guards overpowered. ₹47,32,000 seized. One guard (Ramesh Lal, P0300) injured (blunt trauma to left forearm). Suspects fled in two vehicles: a white Maruti Eeco (untraced) and a black motorcycle (Hero Splendor, plate partially obscured, HR-07AZ-0568 — later confirmed cloned). CCTV from CAM-01 captured all five suspects entering the zone; one (grey tracksuit, 5'10" estimated) kept his face obscured throughout.

**Principal Suspects/Persons:**
- P0002 — Rakesh Yadav (SUSPECT, ARRESTED, CONVICTED) — driver of Eeco, prior robbery conviction
- P0003 — Mohinder Bhati aka "Bhura" (SUSPECT, ARRESTED, CONVICTED) — on-ground coordinator
- P0004 — Ramesh Chauhan (SUSPECT, ARRESTED, CONVICTED) — weapon carrier
- P0005 — Devender Nagar (SUSPECT, ARRESTED, CONVICTED) — motorcycle rider
- PERSON_UNKNOWN_05 (SUSPECT, ABSCONDING) — grey tracksuit, planner role, face obscured
- P0300 — Ramesh Lal (VICTIM) — injured security guard, SBI cash van

**Key Events:**
- EVENT-001: VEHICLE_SIGHTING — HR-07AZ-0568 at CAM-01, 07:38:04, outbound from Najafgarh Road
- EVENT-002: CRIME — Cash van interception, Dwarka Sec 23 T-junction, 07:43:00 (FIR_FILING)
- EVENT-003: DEVICE_PING — T0011 (burner) pings TOWER-DW-01, 07:38:21 (4 min before incident)
- EVENT-004: ARREST — P0002, P0003, P0004, P0005 arrested within 72 hours, Najafgarh area
- EVENT-005: FORENSIC_COLLECTION — Fingerprints, vehicle interior, 2012-03-15

**Evidence Artifacts:**
- EVD-001-001: CAM-01 CCTV still — grey tracksuit figure at 07:43:12 (face obscured)
- EVD-001-002: FIR No. 127/2012, Dwarka PS, handwritten, 14 March 2012
- EVD-001-003: Interrogation transcript — Rakesh Yadav, 2013 prison statement ("Pandit planned the approach")
- EVD-001-004: CDR dump — T0011 tower pings, 2012-03-14 (TOWER-DW-01, 07:38)
- EVD-001-005: Forensic fingerprint report — 4 matched, 1 unmatched latent (PERSON_UNKNOWN_05)
- EVD-001-006: Medico-legal certificate — Ramesh Lal, injury documentation
- EVD-001-007: Seized currency inventory — ₹47,32,000 denominations list

**Hypotheses:**
- H-001-A: "PERSON_UNKNOWN_05 is a known associate of P0002 from Najafgarh area" (ACTIVE, POSSIBLE)
  - Support: EVD-001-003 (alias "Pandit" mentioned), EVD-001-004 (T0011 tower ping)
  - Contradicting: No direct ID confirmation; face obscured in all CCTV frames

**Cross-Case:** CIVIX-028 (alias "Vikram @ Pandit" surfaces 18 months later); CIVIX-003 (device T0011 pings again)
**CIVIX Capabilities:** Graph traversal, alias identity candidate, CDR overlay, evidence explorer

---

## CIVIX-002 | Dacoity — Uttam Nagar Jewellery Showroom (2020)
**Status:** CLOSED_UNSOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Uttam Nagar PS | **Opened:** 2020-06-25

**FIR Narrative:** Armed robbery at Shree Ram Jewellers, Uttam Nagar main market. Four assailants entered at 14:15 on 25 June 2020 posing as customers. One displayed a country-made pistol. Jewellery valued at ₹18.7 lakh seized. Getaway vehicle: white Scorpio, unregistered, abandone on Ring Road. CCTV from shop was non-functional (power cut, possible pre-planned). Witnesses describe assailants as local Haryanvi-accented men.

**Principal Persons:**
- P0006 — Kuldeep Meena (SUSPECT, ABSCONDING) — alleged coordinator, identified by informant
- P0007 — Prabhat Singh (SUSPECT, ABSCONDING) — entered shop first
- P0008 — Ritu Bhai (PERSON_OF_INTEREST) — alleged vehicle provider, never charged
- P0301 — Suresh Agarwal (VICTIM) — showroom owner, filed complaint

**Key Events:**
- EVENT-010: FIR_FILING at Uttam Nagar PS, 2020-06-25 14:45
- EVENT-011: VEHICLE_SIGHTING — white Scorpio abandoned, Ring Road near Janakpuri, 16:22
- EVENT-012: SURVEILLANCE_OBSERVATION — P0006 spotted at Najafgarh market by CI, 2020-07-10 (not acted upon)

**Evidence Artifacts:**
- EVD-002-001: FIR No. 284/2020, Uttam Nagar PS
- EVD-002-002: Witness statements (4 shopkeepers, contradictory height descriptions)
- EVD-002-003: Abandoned vehicle report — white Scorpio, no registration plates found
- EVD-002-004: Informant report — naming P0006 (classified, restricted access)

**Hypotheses:**
- H-002-A: "Kuldeep Meena is a sub-lieutenant in the N1 robbery network" (ACTIVE, POSSIBLE)
- H-002-B: "Robbery was opportunistic, unlinked to N1" (ACTIVE, POSSIBLE, CONTRADICTS H-002-A)
  - Both hypotheses remain unresolved; case CLOSED_UNSOLVED due to lack of actionable leads

**Cross-Case:** CIVIX-004 (Kuldeep Meena appears as informant lead in armed snatching case)
**CIVIX Capabilities:** Competing hypotheses display, evidence contradiction, case workspace

---

## CIVIX-003 | NH-48 Cash Van Dacoity — Unresolved Latent Print (2021) [HERO-04]
**Status:** COLD → REOPENED (triggered by CIVIX-009 AFIS match) | **Priority:** CRITICAL
**Jurisdiction:** Dwarka PS | **Opened:** 2021-11-05

**FIR Narrative:** SBI cash van intercepted on NH-48 near KM 14 milestone on 5 November 2021. Six suspects. ₹63,40,000 seized. Two guards assaulted (one hospitalized). Getaway vehicle: dark green Mahindra Bolero (HR-06UH-3818, subsequently confirmed stolen). Forensics recovered one high-quality latent fingerprint from the steering wheel of the Bolero — no match found in 2021 or 2022. Case went COLD December 2022.

**Principal Persons:**
- P0001 — Suresh Valmiki aka "Suri Bhai" (SUSPECT — identified 2026 via AFIS) — confirmed via latent print
- P0002 — Rakesh Yadav (SUSPECT, PERSON_OF_INTEREST) — MO overlap with CIVIX-001
- P0009 — Manjeet Rawat (SUSPECT, ABSCONDING) — identified by eyewitness, never traced
- P0010 — Unknown Male 1 (SUSPECT) — no identification possible
- P0302 — Guard Santosh Kumar (VICTIM) — hospitalized with head injury

**Key Events:**
- EVENT-020: CRIME — cash van interception, NH-48 KM 14, 2021-11-05 09:17
- EVENT-021: VEHICLE_SIGHTING — HR-06UH-3818 at CAM-02 (NH-48 Toll A), 09:04:33 inbound
- EVENT-022: FORENSIC_COLLECTION — latent print from Bolero steering wheel, 2021-11-05 14:00
- EVENT-023: DEVICE_PING — T0011 pings TOWER-NH-01, 09:11:44 (same day as robbery)
- EVENT-024: MEDICAL_EXAMINATION — P0302 Santosh Kumar, injury report

**Evidence Artifacts:**
- EVD-003-001: Latent fingerprint AFIS card — steering wheel print (2021, UNMATCHED)
- EVD-003-002: EVD-H04-002 — AFIS match result (2026, matched to P0001 ten-print booking)
- EVD-003-003: CAM-02 footage still — HR-06UH-3818, 09:04:33, direction inbound NH-48
- EVD-003-004: FIR No. 891/2021, Dwarka PS
- EVD-003-005: Medical report — Santosh Kumar hospitalization (head trauma, 11 days)
- EVD-003-006: CDR dump — T0011, 2021-11-05, tower pings timeline

**Hypotheses:**
- H-003-A: "Suresh Valmiki coordinated the 2021 NH-48 robbery" (CONFIRMED via AFIS 2026)
- H-003-B: "Manjeet Rawat is still active in NCR robbery circuit" (ACTIVE, POSSIBLE)

**Cross-Case:** CIVIX-001 (T0011 device overlap), CIVIX-009 (AFIS trigger for reopen), CIVIX-044 (financial proceeds)
**CIVIX Capabilities:** Cold case reopen, AFIS biometric match, spatial vehicle correlation, lead generation

---

## CIVIX-004 | Armed Snatching Gang — NH-48 Corridor (2017)
**Status:** COLD | **Priority:** LOW | **Type:** CRIMINAL
**Jurisdiction:** NH-48 Highway Patrol Unit | **Opened:** 2017-02-12

**FIR Narrative:** Series of 7 motorcycle snatching incidents on NH-48 service road between January and February 2017. Suspects: 2–3 person teams on motorcycles. Three victims filed FIRs; others settled informally. Total loss: ₹4.2 lakh (bikes + valuables). One suspect caught (P0011, released on bail, absconded). Pattern: attacks near TOWER-NH-01 coverage zone, 19:00–21:00 hours.

**Principal Persons:**
- P0011 — Kapil Dhankhar (SUSPECT, BAIL ABSCONDER) — caught once, released
- P0012 — Unknown Male 2 (SUSPECT) — accomplice, never identified
- P0303, P0304, P0305 — Victims (VICTIM)

**Evidence Artifacts:**
- EVD-004-001: FIR nos. 89, 90, 114/2017 (three separate FIRs)
- EVD-004-002: CDR dump — P0011's registered phone, pings consistent with crime zone
- EVD-004-003: Victim statements (3) — height/build descriptions conflict

**Cross-Case:** CIVIX-002 (P0011 has common associates with Kuldeep Meena)
**CIVIX Capabilities:** Pattern of crime spatial visualization, CDR overlay

---

## CIVIX-005 | Loot of Bank Cash-in-Transit — Dwarka Sector 23 (2017)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Dwarka PS | **Opened:** 2017-07-06

**FIR Narrative:** Second incident at Dwarka Sector 23 (same location as 2012 robbery — possibly insider knowledge of route). ₹38 lakh looted from ICICI cash van. Three suspects, two motorcycles. No convictions yet. Witness (P0306) saw one suspect previously in the area in January 2017 — possible surveillance run.

**Principal Persons:**
- P0013 — Vikas Gurjar (SUSPECT, CHARGESHEETED) — identified from CAM-01 CCTV (partial face)
- P0014 — Hardeep Mann (SUSPECT, ABSCONDING)
- P0306 — Manoj Kumar Jha (WITNESS) — auto-rickshaw driver, saw possible surveillance run

**Key Events:**
- EVENT-030: SURVEILLANCE_OBSERVATION — P0013 seen near cash point, 2017-01-14 (2 months before robbery)
- EVENT-031: CRIME — cash van interception, 2017-07-06 10:22
- EVENT-032: VEHICLE_SIGHTING — two motorcycles, CAM-01, plate obscured

**Evidence Artifacts:**
- EVD-005-001: CAM-01 still — P0013 face (40% confidence match, partially visible)
- EVD-005-002: FIR No. 412/2017
- EVD-005-003: Witness statement — P0306 (surveillance observation)
- EVD-005-004: CDR — P0013's phone shows proximity to crime zone day before robbery

**Hypotheses:**
- H-005-A: "P0013 conducted reconnaissance of cash van route before the robbery" (PROBABLE)
- H-005-B: "An SBI insider leaked van schedule" (ACTIVE, POSSIBLE — same location as CIVIX-001)

**Cross-Case:** CIVIX-001 (same location, possible insider), CIVIX-009 (Suresh Valmiki connection)

---

## CIVIX-006 | Firearm Recovery & Robbery Conspiracy — Uttam Nagar (2011)
**Status:** OPEN | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Uttam Nagar PS | **Opened:** 2011-08-27

**FIR Narrative:** Two country-made pistols and 11 cartridges recovered from a house in Uttam Nagar during a tenant verification drive. Registered to Santosh Mishra (P0015, deceased 2019). Circumstantial links to planned robbery discussed in recovered chits. No robbery actually committed at time of recovery. Case remains open — weapons traced to Bihar supplier.

**Principal Persons:**
- P0015 — Santosh Mishra (SUSPECT, DECEASED 2019) — original weapon holder
- P0016 — Deepa Mishra (PERSON_OF_INTEREST) — wife, claims ignorance
- P0017 — Bihar Arms Supplier (SUSPECT, UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-006-001: Forensic ballistics report — pistol serial numbers (filed off)
- EVD-006-002: Recovered chit (handwritten robbery plan, partial)
- EVD-006-003: FIR No. 634/2011

**Cross-Case:** CIVIX-020 (similar MO weapon sourcing)

---

## CIVIX-007 | Interstate Robbery Gang — Uttam Nagar Module (2013)
**Status:** COLD | **Priority:** LOW | **Type:** CRIMINAL
**Jurisdiction:** Uttam Nagar PS | **Opened:** 2013-01-09

**FIR Narrative:** Series of 5 chain snatchings and 2 armed robberies attributed to an interstate gang operating out of Rajasthan. Two suspects arrested (chargesheeted), 3 absconded. One of the arrested suspects (P0018) gave testimony about their Delhi contact — never adequately followed up.

**Principal Persons:**
- P0018 — Ramkishan Bairwa (ACCUSED, CONVICTED) — arrested, convicted
- P0019 — Shyam Meena (SUSPECT, ABSCONDING)
- P0307 — Delhi Contact "Suresh Ji" (PERSON_OF_INTEREST, UNIDENTIFIED) — mentioned in P0018's testimony

**Evidence Artifacts:**
- EVD-007-001: FIR No. 23/2013
- EVD-007-002: Chargesheet — P0018 testimony (reference to Delhi contact)
- EVD-007-003: Court conviction order — P0018 (5 years)

**Cross-Case:** CIVIX-044 (P0307 "Suresh Ji" may be Suresh Valmiki, cross-case identity candidate IC-003)

---

## CIVIX-008 | Jewellery Heist — DLF Phase 1 Showroom (2023)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Gurugram PS | **Opened:** 2023-03-18

**FIR Narrative:** Elaborate heist at Tanishq showroom, DLF Phase 1. Three suspects posed as HNI customers. One engaged staff, two accessed display case during distraction. ₹42 lakh in gold/diamond jewellery taken. Suspects fled in Hyundai Creta (HR-07AZ-0999, later found abandoned). CCTV captured suspects' faces partially (caps, masks). One suspect (P0020) identified by a former Tanishq employee who recognized his distinctive walk.

**Principal Persons:**
- P0020 — Birju Jaat (SUSPECT, CHARGESHEETED) — identified by witness
- P0021 — Sunil Gujjar (SUSPECT, ABSCONDING)
- P0022 — Sonia Kumari (SUSPECT, ABSCONDING) — female accomplice, distraction role
- P0308 — Anita Verma (WITNESS) — former Tanishq employee

**Key Events:**
- EVENT-040: VEHICLE_SIGHTING — HR-07AZ-0999 on Gurugram Sector 44 CCTV, 2023-03-18 14:07
- EVENT-041: CRIME — jewellery theft, 2023-03-18 14:22
- EVENT-042: VEHICLE_SIGHTING — HR-07AZ-0999 abandoned, DLF Phase 3 parking, 16:45

**Evidence Artifacts:**
- EVD-008-001: CCTV stills from Tanishq (4 frames showing suspects)
- EVD-008-002: FIR No. 189/2023, Gurugram PS
- EVD-008-003: Witness statement — P0308 (walk identification)
- EVD-008-004: Vehicle recovery report — abandoned Creta

**Cross-Case:** CIVIX-003 (P0020 has common associate with Manjeet Rawat)

---

## CIVIX-009 | Najafgarh Cash-in-Transit Robbery — Suresh Valmiki Apprehended (2026) [HERO-04]
**Status:** ACTIVE | **Priority:** CRITICAL | **Type:** CRIMINAL
**Jurisdiction:** Najafgarh PS | **Opened:** 2026-07-19

**FIR Narrative:** Armed robbery of PNB cash van at Najafgarh Bus Terminal. ₹58 lakh seized. Four suspects. During chase, one suspect (Suresh Valmiki, P0001) apprehended at Najafgarh Railway Crossing. Three suspects escaped. P0001 booked. Standard intake: ten-print fingerprint set pushed to AFIS. Within 6 hours, CIVIX auto-generates LEAD-004: AFIS match to 2021 latent print (CIVIX-003). P0001 is now a confirmed suspect in three separate robbery cases.

**Principal Persons:**
- P0001 — Suresh Valmiki aka "Suri Bhai" (SUSPECT, ARRESTED) — principal accused
- P0023 — Escaped Male 1 (SUSPECT, ABSCONDING)
- P0024 — Escaped Male 2 (SUSPECT, ABSCONDING)
- P0309 — PNB Guard Rajveer Singh (VICTIM)

**Key Events:**
- EVENT-050: CRIME — cash van interception, Najafgarh Bus Terminal, 2026-07-19 08:55
- EVENT-051: ARREST — P0001 apprehended, Najafgarh Railway Crossing, 09:14
- EVENT-052: FORENSIC_COLLECTION — ten-print set, P0001, 2026-07-19 11:30
- EVENT-053: DEVICE_PING — T0011 pings TOWER-NJ-01, 08:51:07 (P0001's phone at crime zone)

**Evidence Artifacts:**
- EVD-009-001: AFIS booking card — Suresh Valmiki ten prints
- EVD-009-002: AFIS match result — 93% confidence match to CIVIX-003 latent
- EVD-009-003: CAM-04 CCTV still — P0001 at Najafgarh Bus Terminal, 08:55
- EVD-009-004: FIR No. 441/2026, Najafgarh PS
- EVD-009-005: CDR — T0011, 2026-07-19, tower pings

**Investigative Lead:** LEAD-004 — "AFIS Biometric Match: Latent Print CIVIX-003 = P0001 (Suresh Valmiki)" score: 0.93, priority: CRITICAL
discovery_vector: {"vector_type": "BIOMETRIC_AFIS_MATCH", "confidence_signals": {"afis_minutiae_score": 0.93, "latent_print_quality": "HIGH"}, "source_case_ids": ["CIVIX-003"], "target_case_id": "CIVIX-009"}

**Cross-Case:** CIVIX-003 (AFIS trigger), CIVIX-001 (MO, same gang), CIVIX-044 (financial proceeds to Dinesh Yadav)

---

# NETWORK N2 — HAWALA & FINANCIAL SHELL COMPANY FRAUD (Cases 010–018)

---

## CIVIX-010 | Chandni Chowk Bank SAR — Shell GST Trail (2026) [HERO-02 trigger]
**Status:** OPEN | **Priority:** CRITICAL | **Type:** FINANCIAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2026-02-11

**FIR Narrative:** HDFC Bank's AML unit filed a Suspicious Activity Report flagging Arham Bullion Traders Pvt Ltd (ORG-031) for 23 credits totaling ₹4.7 crore in 40 days, with no corresponding business activity. Karol Bagh PS opened investigation. During CIVIX ingestion of the SAR PDF, NER extraction pulls GST No. 07AARCA1234J1Z1. CIVIX graph query returns a match to CIVIX-036 entity records — Tariq Hussain's 2018 company documents. Lead LEAD-002 generated. Case CIVIX-036 flagged for investigator review (REOPENED recommendation).

**Principal Persons:**
- P0095 — Tariq Hussain aka "Sona Bhai" (SUSPECT — identified via GST match)
- P0025 — Harish Mehta aka "Seth-ji" (SUSPECT, PRIMARY) — hawala network head
- P0026 — Abdul Razzaq (PERSON_OF_INTEREST) — Arham Bullion Traders registered director (Tariq's nephew)
- P0310 — HDFC AML Officer Nidhi Arora (OFFICER_IN_CHARGE)

**Key Events:**
- EVENT-060: OTHER — Bank SAR filed by HDFC, 2026-02-11
- EVENT-061: TRANSACTION — 23 credits to Arham Bullion Traders, ₹4.7 crore, 40-day window
- EVENT-062: FIR_FILING — Karol Bagh PS, 2026-02-11

**Evidence Artifacts:**
- EVD-010-001: Bank SAR PDF — HDFC Karol Bagh, flagging Arham Bullion Traders (KEY EVIDENCE)
- EVD-010-002: Transaction history extract — Arham Bullion Traders account (23 credits listed)
- EVD-010-003: GST registration certificate — Arham Bullion Traders (07AARCA1234J1Z1)
- EVD-010-004: Company director records — showing P0026 as director, P0095 as beneficial owner

**Investigative Lead:** LEAD-002 — "GST Registration Overlap — Cold Case Linkage (CIVIX-036)" score: 0.94, priority: CRITICAL
discovery_vector: {"vector_type": "DOCUMENT_EXTRACTION_MATCH", "confidence_signals": {"gst_exact_match": 1.0, "address_match_score": 0.96, "pan_exact_match": 1.0}, "source_case_ids": ["CIVIX-036"], "target_case_id": "CIVIX-010"}

**Cross-Case:** CIVIX-036 (GST/cold case linkage — HERO-02), CIVIX-015 (hawala network overlap)

---

## CIVIX-011 | Shell Company GST Fraud — Sadar Bazar (2023)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** FINANCIAL
**Jurisdiction:** Sadar Bazar PS | **Opened:** 2023-08-24

**FIR Narrative:** GST fraud using fictitious invoices. Three shell companies (ORG-032, ORG-033, ORG-034) registered at the same address — a one-room shop in Sadar Bazar. Total fraudulent ITC claimed: ₹8.3 crore over 14 months. Investigation shows invoices for non-existent goods (industrial pipes, raw cotton). ED has been notified.

**Principal Persons:**
- P0025 — Harish Mehta aka "Seth-ji" (SUSPECT, PRIMARY) — beneficial owner of all three shells
- P0027 — Pavan Kumar (ACCUSED, ARRESTED) — registered director, ORG-032
- P0028 — Geeta Devi (ACCUSED, ARRESTED) — registered director, ORG-033 (Pavan's wife)
- P0029 — Ramesh Prasad (PERSON_OF_INTEREST) — CA who filed fraudulent returns

**Key Events:**
- EVENT-070: TRANSACTION — fictitious invoice cycles, ORG-032 to ORG-033, 2022-06-01 to 2023-07-31
- EVENT-071: ARREST — P0027, P0028, 2023-08-24
- EVENT-072: SEIZURE — company documents, laptop, 3 mobile phones from Sadar Bazar premises

**Evidence Artifacts:**
- EVD-011-001: GST fraud forensic audit report — 47-page ED assessment
- EVD-011-002: Fictitious invoices — 156 invoices (sample 20 in evidence file)
- EVD-011-003: Company registration docs — ORG-032, ORG-033, ORG-034 (same address)
- EVD-011-004: Bank statement analysis — round-tripping through 4 accounts
- EVD-011-005: FIR No. 667/2023, Sadar Bazar PS
- EVD-011-006: CA Ramesh Prasad statement (claims duped by Harish Mehta)

**Hypotheses:**
- H-011-A: "Harish Mehta is the beneficial controller of all three shell entities" (PROBABLE)
  - Support: EVD-011-003 (same address), EVD-011-004 (bank flow analysis)
  - Neutral: EVD-011-006 (CA claims ignorance — neither supports nor contradicts)
- H-011-B: "ITC fraud proceeds funded N1 robbery network via cash hawala" (POSSIBLE)
  - Support: P0025's known associates include P0001 (Suresh Valmiki)

**Cross-Case:** CIVIX-010 (Harish Mehta same suspect), CIVIX-044 (proceeds to real estate)

---

## CIVIX-012 | Suspicious Fund Trail — Sadar Bazar Exchange (2018)
**Status:** OPEN | **Priority:** MEDIUM | **Type:** FINANCIAL
**Jurisdiction:** Sadar Bazar PS | **Opened:** 2018-09-10

**FIR Narrative:** Complaint by ED regarding unusually large cash deposits (₹2.1 crore) at a Sadar Bazar money exchange (ORG-035) within 72 hours of a known robbery (CIVIX-009 predecessor). No direct evidence linking exchange to robbery; exchange owner claims legitimate trade.

**Principal Persons:**
- P0030 — Fazal Ansari (SUSPECT, PERSON_OF_INTEREST) — owner, ORG-035
- P0031 — Neeraj Saini (WITNESS) — bank teller who flagged unusual deposits

**Evidence Artifacts:**
- EVD-012-001: Bank deposit records — ORG-035 account, three large deposits
- EVD-012-002: Fazal Ansari statement — claims wholesale textile trade as source
- EVD-012-003: Textile trade receipts (P0030's claim — cannot be independently verified)

**Hypotheses:**
- H-012-A: "Fazal Ansari laundered robbery proceeds through ORG-035" (POSSIBLE)
- H-012-B: "Deposits are legitimate textile trade proceeds" (POSSIBLE, unresolved)

**Cross-Case:** CIVIX-009 (timing overlap with robbery proceeds), CIVIX-011 (Harish Mehta associate network)

---

## CIVIX-013 | Bank SAR — Hawala Probe, Karol Bagh (2019)
**Status:** COLD | **Priority:** LOW | **Type:** FINANCIAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2019-11-26

**FIR Narrative:** Punjab National Bank flagged hawala-style remittances through Karol Bagh branch. Three accounts showing structuring (multiple sub-₹2-lakh deposits in same day). Case investigated, no arrests made, insufficient evidence to charge. Links to N2 network probable but not established.

**Principal Persons:**
- P0032 — Anil Kapoor (not the actor) (PERSON_OF_INTEREST) — account holder, one of three
- P0033 — Sunita Rani (PERSON_OF_INTEREST) — account holder
- P0034 — Mohammad Arif (PERSON_OF_INTEREST) — account holder

**Evidence Artifacts:**
- EVD-013-001: PNB SAR report — structuring pattern analysis
- EVD-013-002: Account statements — all three accounts (KYC documents)

**Cross-Case:** CIVIX-011 (similar structuring pattern, different branch)

---

## CIVIX-014 | Cross-Border Hundi Network — Sadar Bazar (2016)
**Status:** COLD | **Priority:** MEDIUM | **Type:** FINANCIAL
**Jurisdiction:** Sadar Bazar PS | **Opened:** 2016-08-15

**FIR Narrative:** Enforcement Directorate investigation into informal cross-border remittances (hundi system) operating through Sadar Bazar. Amounts transferred to Dubai and Sharjah without RBI authorization. Total detected: ₹12.4 crore. Two operators identified; one fled to UAE.

**Principal Persons:**
- P0035 — Rafiq Ahmed (SUSPECT, ABSCONDING — UAE) — primary hundi operator
- P0036 — Aziz Bhai (SUSPECT, ABSCONDING) — Dubai receiver

**Evidence Artifacts:**
- EVD-014-001: ED FEMA complaint
- EVD-014-002: Swift message analysis (correspondent bank intercepts)
- EVD-014-003: Interpol Red Notice — P0035 (issued 2017)

**Cross-Case:** CIVIX-010 (Arham Bullion Traders referenced in hundi records)

---

## CIVIX-015 | Fictitious Invoicing Ring — Karol Bagh (2022)
**Status:** OPEN | **Priority:** HIGH | **Type:** FINANCIAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2022-08-21

**FIR Narrative:** Complex multi-layer fictitious invoicing scheme. ORG-036 (electronics trading) issued invoices for goods never supplied. GSTN analytics flagged the discrepancy. Case linked to two other shell entities in Noida Sector 62.

**Principal Persons:**
- P0037 — Vinod Khanna (SUSPECT, CHARGESHEETED) — director, ORG-036
- P0038 — Seema Khanna (PERSON_OF_INTEREST) — spouse and co-director
- P0039 — CA Sudhir Jain (ACCUSED) — prepared fraudulent returns

**Evidence Artifacts:**
- EVD-015-001: GSTN analytics report — mismatch between GSTR-1 and GSTR-2
- EVD-015-002: Company audit — ORG-036 physical inspection (empty office)
- EVD-015-003: Bank statements — fund flow analysis
- EVD-015-004: FIR No. 544/2022

**Cross-Case:** CIVIX-011 (Harish Mehta beneficial interest suspected — unconfirmed), CIVIX-036 (Gold theft proceeds allegedly invested through this network)

---

## CIVIX-016 | Money Laundering — Chandni Chowk Bullion Traders (2021)
**Status:** COLD | **Priority:** MEDIUM | **Type:** FINANCIAL
**Jurisdiction:** Chandni Chowk PS | **Opened:** 2021-02-15

**FIR Narrative:** ED notice to three bullion traders in Chandni Chowk for large cash transactions without PAN/Aadhaar disclosure. Traders claim all purchases from scrap dealers. Two traders paid compounding fees; one (P0040) refused and case escalated.

**Principal Persons:**
- P0040 — Chandrakant Shah (SUSPECT, CHARGESHEETED) — refused compounding

**Evidence Artifacts:**
- EVD-016-001: ED survey report — premises search, Chandni Chowk
- EVD-016-002: Cash transaction records (unaccounted)

---

## CIVIX-017 | Benami Transaction — Lajpat Nagar Property (2020)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** PROPERTY
**Jurisdiction:** Lajpat Nagar PS | **Opened:** 2020-05-12

**FIR Narrative:** A commercial property in Lajpat Nagar (Shop No. 14, South Extension) registered in the name of P0041 (Meena Devi, daily wage worker) was found to be actually controlled by Harish Mehta (P0025). Benami Transactions Prohibition Act case. ₹3.8 crore property value. Meena Devi claims she signed papers without understanding them.

**Principal Persons:**
- P0025 — Harish Mehta (SUSPECT, BENEFICIAL OWNER)
- P0041 — Meena Devi (ACCUSED — benami holder, cooperating witness)

**Evidence Artifacts:**
- EVD-017-001: Property registration document — in P0041's name
- EVD-017-002: Bank statement — mortgage EMIs paid from P0025's shell company account
- EVD-017-003: Meena Devi statement (cooperating)
- EVD-017-004: Land registry — property valuation

**Cross-Case:** CIVIX-011 (Harish Mehta is primary suspect in both)

---

## CIVIX-018 | Shell Company Director Network — Noida Sector 62 (2024)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** FINANCIAL
**Jurisdiction:** Noida PS | **Opened:** 2024-01-08

**FIR Narrative:** MCA21 analytics detected a cluster of 12 companies sharing 3 directors in rotation — each director appears on 4 companies simultaneously. One of the directors is P0042 (Rahul Verma, 24 years old, listed as director of 4 companies while claiming to be a student). Companies show high GST turnover but no GST payment history.

**Principal Persons:**
- P0042 — Rahul Verma (ACCUSED) — student director, multiple companies
- P0043 — Priya Sharma (ACCUSED) — student director (classmate of P0042)
- P0044 — Mastermind UNKNOWN (PERSON_OF_INTEREST) — who recruited them

**Evidence Artifacts:**
- EVD-018-001: MCA21 company network analysis
- EVD-018-002: College enrollment records — P0042, P0043 (alibi partial)
- EVD-018-003: Bank KYC — both show same IP address for net banking login

**Cross-Case:** CIVIX-011 (similar pattern, potential Harish Mehta mastermind hypothesis IC-005)

---

# NETWORK N3 — LUXURY VEHICLE THEFT & PLATE CLONING (Cases 019–026)

---

## CIVIX-019 | Toll-Plaza ANPR Spatial Paradox — Cloned Fortuner (2026) [HERO-03]
**Status:** ACTIVE | **Priority:** CRITICAL | **Type:** CRIMINAL
**Jurisdiction:** Mayapuri PS | **Opened:** 2026-04-03

**FIR Narrative:** ANPR system flags a Toyota Fortuner (DL-8C-AB-1234) appearing at two geographically impossible locations within 3 minutes. PostGIS analysis confirms 14.7 km separation; speed required = 321 km/h. CIVIX DQ issue flagged: SPATIAL_IMPOSSIBILITY. Investigation opened. Original vehicle owner (Ravi Malhotra, P0050) confirmed his vehicle was at home that morning. Clone investigation leads to Mayapuri chop-shop cluster.

**Principal Persons:**
- P0045 — Joginder "Jogi" Kalra (SUSPECT, PRIMARY) — plate cloning ring head
- P0046 — Pawan Sharma (SUSPECT) — Fortuner clone operator
- P0047 — Deepak Tyagi (SUSPECT) — Mayapuri workshop operator
- P0050 — Ravi Malhotra (COMPLAINANT) — legitimate owner of original DL-8C-AB-1234

**Key Events:**
- EVENT-090: VEHICLE_SIGHTING — DL-8C-AB-1234 at CAM-02 (NH-48 Toll A), 2026-04-03 14:22:07
- EVENT-091: VEHICLE_SIGHTING — DL-8C-AB-1234 at CAM-15 (Nizamuddin approach), 2026-04-03 14:24:51
- EVENT-092: OTHER — CIVIX DQ issue created: SPATIAL_IMPOSSIBILITY, 2026-04-03 17:00 (batch processing)
- EVENT-093: SEIZURE — Mayapuri workshop raided, clone Fortuner (different VIN, same plate), 2026-04-15

**Evidence Artifacts:**
- EVD-019-001: ANPR crop — CAM-02, DL-8C-AB-1234, 14:22:07 (front-facing, plate sharp)
- EVD-019-002: ANPR crop — CAM-15, DL-8C-AB-1234, 14:24:51 (front-facing, different lighting)
- EVD-019-003: PostGIS distance analysis — map showing two camera points, 14.72 km distance annotation
- EVD-019-004: Vehicle registration — DL-8C-AB-1234, Ravi Malhotra, original VIN
- EVD-019-005: VIN inspection report — clone vehicle (different VIN, same plate)
- EVD-019-006: CIVIX ANPR timeline — all 14 sightings of DL-8C-AB-1234 (6-month range)
- EVD-019-007: FIR No. 223/2026, Mayapuri PS
- EVD-019-008: Mayapuri workshop raid report — seized tools, blank plates, VIN stamps

**Investigative Lead:** LEAD-003 — "ANPR Spatial Paradox — Vehicle Cloning Confirmed" score: 0.95, priority: CRITICAL
discovery_vector: {"vector_type": "SPATIAL_IMPOSSIBILITY", "confidence_signals": {"speed_kmh": 321, "distance_meters": 14720, "time_seconds": 164, "physical_max_speed": 220}, "source_case_ids": ["CIVIX-019"], "target_case_id": "CIVIX-022"}

**Cross-Case:** CIVIX-022 (same chop-shop), CIVIX-003 (clone used in robbery corridor)

---

## CIVIX-020 | ANPR Plate-Cloning Detection — Karol Bagh (2025)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2025-10-11

**FIR Narrative:** Routine ANPR audit identified 6 vehicles whose plates appeared at locations inconsistent with their registered home state or district at the same time as a confirmed sighting elsewhere. Three plates confirmed as cloned. Karol Bagh spare parts market identified as primary plate sourcing location.

**Principal Persons:**
- P0048 — Mithun Das (SUSPECT, ARRESTED) — operating clone plates in Karol Bagh
- P0049 — Plate Supplier (UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-020-001: ANPR audit report — 6 vehicles flagged, 3 confirmed clones
- EVD-020-002: Karol Bagh spare parts market CCTV (partial face, plate transaction)
- EVD-020-003: FIR No. 1102/2025

**Cross-Case:** CIVIX-019 (same plate cloning ring), CIVIX-026 (one cloned plate used in chop-shop delivery)

---

## CIVIX-021 | Stolen Vehicle Chop-Shop — Karol Bagh (2019)
**Status:** CLOSED_UNSOLVED | **Priority:** LOW | **Type:** CRIMINAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2019-05-01

**FIR Narrative:** Three stolen SUVs recovered in dismantled state from a basement workshop in Karol Bagh. Operator fled; premises rented under false name. No arrests. VINs traced to vehicles stolen from Gurugram and Faridabad (2018–2019).

**Evidence Artifacts:**
- EVD-021-001: Workshop raid report — tools, partial VINs, vehicle parts
- EVD-021-002: VIN trace — 3 original vehicle theft FIRs (Gurugram, Faridabad)
- EVD-021-003: Rental agreement (false identity)

**Cross-Case:** CIVIX-022 (same VIN-stamping technique used in Mayapuri), CIVIX-019 (chop-shop network)

---

## CIVIX-022 | Engine/Chassis Re-stamping — Mayapuri (2021)
**Status:** OPEN | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Mayapuri PS | **Opened:** 2021-10-26

**FIR Narrative:** Three Mayapuri industrial units found to be operating illegal engine and chassis re-stamping equipment. Seven vehicles with tampered VINs seized. Workshop operators (P0047 Deepak Tyagi and P0051 Harnam Singh) arrested. Evidence suggests operation began 2018, served N1 robbery network with untraceable vehicles.

**Principal Persons:**
- P0047 — Deepak Tyagi (ACCUSED, ARRESTED) — workshop operator
- P0051 — Harnam Singh (ACCUSED, ARRESTED) — VIN stamping specialist
- P0052 — Client Unknown (7 clients, UNIDENTIFIED)

**Key Events:**
- EVENT-100: SEIZURE — 7 vehicles, 3 workshops, Mayapuri Phase 2, 2021-10-26
- EVENT-101: ARREST — P0047, P0051, 2021-10-26

**Evidence Artifacts:**
- EVD-022-001: VIN comparison report — original vs. re-stamped chassis numbers
- EVD-022-002: Tool seizure report — industrial VIN stamps
- EVD-022-003: Vehicle history trace — 7 seized vehicles, original theft FIRs
- EVD-022-004: FIR No. 789/2021, Mayapuri PS
- EVD-022-005: Deepak Tyagi statement (partial — claims ignorance of vehicle origins)

**Cross-Case:** CIVIX-019 (clone Fortuner linked to this workshop), CIVIX-003 (Bolero used in robbery traced to similar workshop)

---

## CIVIX-023 | Cross-State Vehicle Smuggling — Tilak Nagar (2022)
**Status:** CLOSED_SOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Tilak Nagar PS | **Opened:** 2022-11-14

**FIR Narrative:** Intercept of a truck transporting 4 luxury vehicles (Fortuner, 2 Creetas, BMW) with tampered VINs headed to Rajasthan. All vehicles confirmed stolen from NCR. Three suspects arrested and convicted.

**Principal Persons:**
- P0053 — Rajesh Sharma (ACCUSED, CONVICTED) — truck driver
- P0054 — Naresh Kumar (ACCUSED, CONVICTED) — vehicle loader
- P0055 — Broker Unknown (SUSPECT, ABSCONDING)

**Evidence Artifacts:**
- EVD-023-001: Seizure report — 4 vehicles, tampered VINs
- EVD-023-002: Conviction order — P0053, P0054

---

## CIVIX-024 | Fake RC Registration Racket — Karol Bagh RTO (2025)
**Status:** OPEN | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Karol Bagh PS | **Opened:** 2025-02-17

**FIR Narrative:** RTO Karol Bagh discovered 34 fraudulent vehicle Registration Certificates (RCs) issued over 18 months. A corrupt RTO clerk (P0056, Suresh Yadav — no relation to robbery Yadavs) accepted ₹8,000–₹15,000 per RC. Vehicles registered under fake owner names. 12 of 34 vehicles subsequently found in theft-linked cases.

**Principal Persons:**
- P0056 — Suresh Yadav, RTO Clerk (ACCUSED, ARRESTED) — corrupt official
- P0057 — RC Broker Ramu (SUSPECT, ABSCONDING) — intermediary, ran the supply chain
- P0045 — Joginder "Jogi" Kalra (SUSPECT) — primary buyer of fake RCs (cross-case)

**Evidence Artifacts:**
- EVD-024-001: RTO audit — 34 fraudulent RCs identified
- EVD-024-002: CCTV — Suresh Yadav accepting cash at RTO counter
- EVD-024-003: P0056 bank statement — suspicious cash deposits matching RC dates
- EVD-024-004: FIR No. 134/2025

**Cross-Case:** CIVIX-001 (fake RC used on robbery getaway bike), CIVIX-019 (clone Fortuner had fake RC)

---

## CIVIX-025 | Odometer & VIN Tampering — Tilak Nagar (2011)
**Status:** CLOSED_SOLVED | **Priority:** LOW | **Type:** CRIMINAL
**Jurisdiction:** Tilak Nagar PS | **Opened:** 2011-03-12

**FIR Narrative:** Historic case. Two operators convicted for odometer tampering and VIN alteration on used vehicles. Included as universe background case — demonstrates long-running nature of vehicle crime in this corridor.

**Evidence Artifacts:** EVD-025-001: Conviction order (2013)

---

## CIVIX-026 | Luxury Bike Theft Ring — Vasant Kunj to Mayapuri (2024)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Vasant Kunj PS | **Opened:** 2024-07-22

**FIR Narrative:** 18 luxury motorcycles (Royal Enfield, KTM, BMW bikes) stolen from upscale residential areas (Vasant Kunj, Saket, GK-II) over 5 months. All found dismantled in Mayapuri. Theft-to-chop-shop pipeline confirmed via CCTV tracking of same motorcycle carrying stolen bikes on roof rack.

**Principal Persons:**
- P0058 — Sonu Bike (alias, real name unknown, SUSPECT) — identified by informant only
- P0059 — Rakesh Namdev (SUSPECT, ARRESTED) — Mayapuri receiver

**Evidence Artifacts:**
- EVD-026-001: CCTV chain — stolen bike rooftop transport from Vasant Kunj to Mayapuri
- EVD-026-002: Mayapuri parts seizure — 18 bikes' worth of components

**Cross-Case:** CIVIX-022 (Mayapuri chop-shop, P0047 Deepak Tyagi connection)

---

# NETWORK N4 — CYBER EXTORTION & DIGITAL ARREST FRAUD (Cases 027–035)

---

## CIVIX-027 | Digital Arrest Call Center — Rohini (2021) + The Fifth Robber Alias Link [HERO-01 chain]
**Status:** CLOSED_SOLVED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Rohini PS | **Opened:** 2021-09-02

**FIR Narrative:** Call center operation in Rohini Sector 16. 23 operators impersonating CBI/Narcotics officials, threatening victims with "digital arrest" and demanding ₹50,000–₹5 lakh payments. Total victims: 156. Total defrauded: ₹1.8 crore. During investigation, interrogation of operator Nitesh Goyal (P0071) reveals recruiter was "Vikram @ Pandit." This alias match triggers LEAD-001.

**Principal Persons:**
- P0070 — Aakash Verma aka "AV Sir" (ACCUSED, ARRESTED) — call center head
- P0071 — Nitesh Goyal (ACCUSED, ARRESTED) — operator, gave "Vikram @ Pandit" testimony
- P0072 — Sonia Rathore (ACCUSED, ARRESTED) — script writer
- P0075 — Vikram Sharma aka "Vikram @ Pandit" (SUSPECT, ABSCONDING) — recruiter, = PERSON_UNKNOWN_05 from CIVIX-001
- P0311 — Victim Ramesh Agarwal (VICTIM) — one of 156

**Key Events:**
- EVENT-110: SURVEILLANCE_OBSERVATION — call center identified by cyber cell, 2021-08-15
- EVENT-111: ARREST — 23 operators including P0070, P0071, P0072, 2021-09-02
- EVENT-112: OTHER — Interrogation of P0071, "Vikram @ Pandit" testimony, 2021-09-05
- EVENT-113: DEVICE_PING — T0011 pings TOWER-RH-01 during active fraud period (same device from CIVIX-001)

**Evidence Artifacts:**
- EVD-027-001: Interrogation transcript — Nitesh Goyal (explicit mention of "Vikram @ Pandit")
- EVD-027-002: CDR dump — T0011, TOWER-RH-01 pings during 2021 fraud operations
- EVD-027-003: Call recordings — sample fraud calls
- EVD-027-004: Victim statement compilation — 156 victims
- EVD-027-005: FIR No. 678/2021, Rohini PS
- EVD-027-006: Money trail — victim payments traced to mule accounts

**Investigative Lead:** LEAD-001 — "Alias-Device Overlap: PERSON_UNKNOWN_05 (CIVIX-001) = Vikram Sharma (CIVIX-027)"
score: 0.87, priority: HIGH
discovery_vector: {"vector_type": "ALIAS_DEVICE_OVERLAP", "confidence_signals": {"alias_match_confidence": 0.88, "device_overlap_confirmed": true, "tower_temporal_overlap_minutes": 4, "corroborating_cases": 2}, "source_case_ids": ["CIVIX-001"], "target_case_id": "CIVIX-027"}

**Cross-Case:** CIVIX-001 (HERO-01 alias + device link), CIVIX-032 (Farrukh Tashkentov connection)

---

## CIVIX-028 | Digital Arrest Scam — Greater Noida Module (2022)
**Status:** REOPENED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Greater Noida PS | **Opened:** 2022-03-08

**FIR Narrative:** Separate digital arrest operation from Greater Noida, operated independently from Rohini module. 67 victims, ₹94 lakh defrauded. Case initially closed. Reopened when CIVIX cross-matched phone numbers from CIVIX-027 CDR dump to numbers appearing in victim complaint lists here — confirming infrastructure sharing.

**Principal Persons:**
- P0073 — Farrukh Tashkentov (SUSPECT, PERSON_OF_INTEREST) — Uzbek national, coordinator
- P0074 — Mohit Sharma (ACCUSED, ARRESTED)
- P0076 — Deepti Arora (ACCUSED, ARRESTED) — scripts and payment coordination

**Evidence Artifacts:**
- EVD-028-001: Cross-CDR analysis — CIVIX-027 numbers appearing in victim statements
- EVD-028-002: FIR No. 234/2022
- EVD-028-003: Farrukh Tashkentov visa overstay documentation

**Cross-Case:** CIVIX-027 (CDR infrastructure overlap), CIVIX-032 (Farrukh connection to call center network)

---

## CIVIX-029 | Sextortion & Blackmail Ring — Shahdara (2020)
**Status:** COLD | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Shahdara PS | **Opened:** 2020-04-27

**FIR Narrative:** 34 victims (mostly men) lured into video calls with fake female profiles, recorded in compromising positions, blackmailed for ₹20,000–₹2 lakh. Operating out of Shahdara, with Mewat connections. Two operators identified but fled.

**Principal Persons:**
- P0077 — Raju Nai (SUSPECT, ABSCONDING) — Mewat connection
- P0078 — Deepak Bihari (SUSPECT, ABSCONDING)

**Evidence Artifacts:**
- EVD-029-001: Victim statements compilation
- EVD-029-002: Fake social media profiles (screenshots)
- EVD-029-003: Bank account — mule account receiving payments

---

## CIVIX-030 | KYC Update Phishing Ring — Shahdara (2023)
**Status:** REOPENED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Shahdara PS | **Opened:** 2023-10-16

**FIR Narrative:** Mass phishing campaign impersonating SBI/HDFC KYC update notifications. 89 victims across NCR. Mule account network traced to Shahdara. Reopened when new victim (2024) provides phone number matching CDR from original investigation.

**Principal Persons:**
- P0079 — Parveen Gujjar (SUSPECT, CHARGESHEETED) — mule account manager
- P0080 — Kavita Jain (ACCUSED, ARRESTED) — sim card procurer

**Evidence Artifacts:**
- EVD-030-001: Phishing message samples (WhatsApp forwards)
- EVD-030-002: Mule account analysis — 12 accounts across 4 banks
- EVD-030-003: SIM card procurement chain — 34 SIMs traced to P0080

**Cross-Case:** CIVIX-028 (same phishing infrastructure, different front)

---

## CIVIX-031 | Fake Customs Officer Call Scam — Rohini (2026)
**Status:** COLD | **Priority:** LOW | **Type:** CRIMINAL
**Jurisdiction:** Rohini PS | **Opened:** 2026-10-08

**FIR Narrative:** Victims receive calls claiming their family member's parcel was intercepted with drugs; pay ₹50,000–₹2 lakh to avoid "arrest." 12 victims in October 2026. Phone numbers traced to Rohini area; operators not yet identified.

**Principal Persons:** Unknown operators (PERSON_OF_INTEREST)

**Evidence Artifacts:**
- EVD-031-001: Victim statements (12)
- EVD-031-002: Call trace report — Rohini TOWER-RH-02 pings

---

## CIVIX-032 | OTP Fraud Call Centre — Greater Noida (2020)
**Status:** REOPENED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Greater Noida PS | **Opened:** 2020-10-09

**FIR Narrative:** Call center in Greater Noida's Knowledge Park III obtained victim OTPs by posing as bank recovery agents. 200+ victims, ₹2.3 crore defrauded. Original case partially closed (some operators arrested). Reopened: new arrests in 2024 linked to same call center through phone number overlap.

**Principal Persons:**
- P0073 — Farrukh Tashkentov (SUSPECT) — behavioral model high-signal subject
- P0081 — Ramesh BPO (alias, ACCUSED, ARRESTED 2024)

**XGBoost Profile — P0073 Farrukh Tashkentov:**
- total_calls: 847 (30 days)
- night_call_ratio: 0.73
- contact_concentration: 0.91
- unique_counterparties: 12 (financial)
- high_value_txn_ratio: 0.34
- geo_spread_degrees: 0.12 (stays in Greater Noida)
- Model Score: 0.84 — HIGH behavioral anomaly

**Evidence Artifacts:**
- EVD-032-001: CDR dump — T0073 (Farrukh's SIM), 30-day analysis
- EVD-032-002: XGBoost behavioral score report — P0073
- EVD-032-003: Mule account transaction analysis
- EVD-032-004: FIR No. 1189/2020

**Cross-Case:** CIVIX-027 (infrastructure overlap), CIVIX-028 (P0073 coordination role)

---

## CIVIX-033 | Loan App Extortion — Greater Noida (2024)
**Status:** OPEN | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Greater Noida PS | **Opened:** 2024-05-25

**FIR Narrative:** Predatory loan app operation. Victims download app, provide contacts and photos. When they miss a repayment, operators harass them and their contacts with morphed/embarrassing images. Operating from Greater Noida server infrastructure.

**Principal Persons:**
- P0082 — App Backend Operator (SUSPECT, UNIDENTIFIED — IP in Guangzhou)
- P0083 — Indian Agent Suresh (SUSPECT, PERSON_OF_INTEREST)

**Evidence Artifacts:**
- EVD-033-001: App store complaint records
- EVD-033-002: Server log extract (limited — hosted abroad)
- EVD-033-003: Victim statement compilation (41 victims)

---

## CIVIX-034 | Impersonation of ED Officers — Preet Vihar (2022)
**Status:** COLD | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Preet Vihar PS | **Opened:** 2022-06-14

**FIR Narrative:** Two suspects impersonating ED officers raided a businessman's home, presented fake ID cards, took ₹8.5 lakh in cash and gold claiming "seizure." Classic impersonation-of-authority crime.

**Principal Persons:**
- P0084 — Mukesh Thakur (SUSPECT, ABSCONDING) — fake ED officer
- P0085 — Sunil Bhai (SUSPECT, ABSCONDING) — accomplice
- P0312 — Victim Arun Sharma (VICTIM) — businessman

**Evidence Artifacts:**
- EVD-034-001: Victim statement — detailed description of fake ID cards
- EVD-034-002: Fake ID cards — recovered at a different location (linked by forensic ink analysis)
- EVD-034-003: CCTV from victim's residential colony — partial vehicle plate

---

## CIVIX-035 | Investment Fraud Call Center — Bawana (2023)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Bawana PS | **Opened:** 2023-09-18

**FIR Narrative:** "Stock market investment" fraud call center in Bawana Industrial Area. Victims lured into WhatsApp groups showing fake profits, then induced to invest ₹5–50 lakh. ₹4.1 crore defrauded from 34 HNI victims. Operation discovered via victim complaint to SEBI.

**Principal Persons:**
- P0086 — Ankit Rawat (ACCUSED, ARRESTED) — call center operator
- P0087 — Priyanka Sharma (ACCUSED, ARRESTED) — WhatsApp group manager
- P0088 — Offshore backend (SUSPECT, UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-035-001: WhatsApp group export — fake profit screenshots
- EVD-035-002: Bank account analysis — victim funds to 7 mule accounts
- EVD-035-003: SEBI complaint and referral letter

---

# NETWORK N5 — CONTRABAND & GOLD SMUGGLING (Cases 036–043)

---

## CIVIX-036 | Nizamuddin Gold Bar Theft (2018) [HERO-02]
**Status:** REOPENED (triggered by CIVIX-010 GST match) | **Priority:** CRITICAL | **Type:** CRIMINAL
**Jurisdiction:** Nizamuddin PS | **Opened:** 2018-06-21

**FIR Narrative:** Seven gold bars (total 2.1 kg, value ₹63.4 lakh at 2018 prices) stolen from an authorized bullion courier at Nizamuddin Railway Station platform 3. The courier, Mehmood Ali (P0313), was intercepted between the platform and exit. One assailant slashed his bag; two others formed a crowd screen. Case investigated. Primary suspect: Tariq Hussain (P0095), who was a known acquaintance of Mehmood Ali. Tariq's company documents showed possible motive. Insufficient evidence to prosecute in 2018; case CLOSED_UNSOLVED.

**In 2026:** CIVIX-010 SAR ingestion triggers NER extraction of GST 07AARCA1234J1Z1 → exact match to Tariq's 2018 company documents → case REOPENED, Lead LEAD-002 generated.

**Principal Persons:**
- P0095 — Tariq Hussain aka "Sona Bhai" (SUSPECT — now CONFIRMED via GST) — mastermind
- P0096 — Priya Sidhu (SUSPECT) — customs clearing agent, facilitated courier access
- P0097 — Joseph Fernandez (SUSPECT, ABSCONDING) — physical thief
- P0313 — Mehmood Ali (VICTIM) — bullion courier, injured

**Key Events:**
- EVENT-140: CRIME — gold bar theft, Nizamuddin Station platform 3, 2018-06-21 16:35
- EVENT-141: FORENSIC_COLLECTION — fingerprints, bag, platform CCTV collected, 2018-06-21
- EVENT-142: OTHER — HDFC Bank SAR filed → CIVIX NER extraction → GST match, 2026-02-11

**Evidence Artifacts:**
- EVD-036-001: FIR No. 312/2018, Nizamuddin PS
- EVD-036-002: Nizamuddin Station CCTV stills — 3 frames showing the theft sequence
- EVD-036-003: Tariq Hussain's 2018 company registration documents (GST 07AARCA1234J1Z1)
- EVD-036-004: Mehmood Ali medical/injury report
- EVD-036-005: 2026 GST match analysis (CIVIX extraction output)
- EVD-036-006: Financial audit — Arham Bullion Traders transaction history post-2018

**Hypotheses:**
- H-036-A: "Tariq Hussain orchestrated the 2018 theft and laundered proceeds via Arham Bullion Traders" (PROBABLE → CONFIRMED with GST match)
- H-036-B: "Priya Sidhu provided internal courier schedule to Tariq" (ACTIVE, POSSIBLE)
  - Support: CDR shows P0095-P0096 contact 2 days before theft
  - Contradicting: No direct evidence Priya knew plans; could be social contact

**Cross-Case:** CIVIX-010 (GST trigger for reopen), CIVIX-038 (IGI cargo network, same smuggling syndicate)

---

## CIVIX-037 | Contraband Seizure — IGI Cargo Terminal (2020)
**Status:** CLOSED_UNSOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** IGI Airport Cargo PS | **Opened:** 2020-02-11

**FIR Narrative:** 4.3 kg of refined gold concealed inside industrial machine parts (declared as "spares for textile machinery") intercepted at IGI Airport Cargo Terminal Gate 3. Importer company (ORG-040) found to be a shell. No arrests made; shipping agent (P0098 Meena Nair) claims ignorance.

**Principal Persons:**
- P0098 — Meena Nair (PERSON_OF_INTEREST) — customs clearing agent
- P0099 — ORG-040 Director (UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-037-001: Customs seizure report — 4.3 kg gold, IGI Cargo
- EVD-037-002: Importer company records — ORG-040 (shell, registered in Noida)
- EVD-037-003: X-ray scan report — showing concealment method

**Cross-Case:** CIVIX-036 (same smuggling network, Tariq Hussain suspected)

---

## CIVIX-038 | Gold Bar Concealment — Okhla Industrial Area (2025)
**Status:** REOPENED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** Okhla Industrial Area PS | **Opened:** 2025-12-27

**FIR Narrative:** 11.2 kg of gold bars discovered during a routine GST inspection of an Okhla Industrial unit (ORG-041 — supposedly a leather goods manufacturer). Gold bars bore foreign mint marks (Dubai). Unit owner (P0100 Mohammed Irfan Qureshi) arrested. He has a BORDER_CROSSING event at Wagah (2024-11-15, outbound to Pakistan), with a ₹14 lakh bank transfer 3 days prior.

**Principal Persons:**
- P0100 — Mohammed Irfan Qureshi (ACCUSED, ARRESTED) — unit owner
- P0095 — Tariq Hussain (SUSPECT) — suspected gold supply source

**Key Events:**
- EVENT-150: SEIZURE — 11.2 kg gold, Okhla Industrial unit, 2025-12-27
- EVENT-151: BORDER_CROSSING — P0100, Wagah outbound, 2024-11-15
- EVENT-152: TRANSACTION — ₹14 lakh transfer from P0100's account to Dubai intermediary, 2024-11-12

**Evidence Artifacts:**
- EVD-038-001: GST inspection report — Okhla Industrial unit
- EVD-038-002: Gold seizure report — 11.2 kg, foreign mint marks (Dubai hallmark)
- EVD-038-003: Border crossing record — P0100, Wagah 2024-11-15
- EVD-038-004: Bank statement — ₹14 lakh transfer, 3 days before border crossing
- EVD-038-005: FIR No. 1456/2025

**Investigative Lead:** LEAD-038 — "Pre-departure Large Transfer + Border Crossing — Financial Flight Risk"
score: 0.71, priority: HIGH

**Cross-Case:** CIVIX-036 (Tariq Hussain network), CIVIX-037 (IGI cargo same gold supply chain)

---

## CIVIX-039 | Courier-Route Gold Smuggling — Nizamuddin (2022)
**Status:** CLOSED_SOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Nizamuddin PS | **Opened:** 2022-03-11

**FIR Narrative:** A commercial courier (ORG-042) was found transporting undeclared gold concealed in power bank packaging. Systematic operation — 14 parcels over 3 months, approximately 2 kg total. Courier operator convicted.

**Principal Persons:**
- P0101 — Karim Ansari (ACCUSED, CONVICTED) — courier operator
- P0102 — Gold Supplier (UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-039-001: Seizure report — concealed gold in power banks
- EVD-039-002: Courier tracking records — 14 parcel trail
- EVD-039-003: Conviction order — P0101

---

## CIVIX-040 | Customs Collusion Probe — IGI Airport (2023)
**Status:** CLOSED_SOLVED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** IGI Airport Cargo PS | **Opened:** 2023-02-08

**FIR Narrative:** Two customs officials at IGI Airport Cargo found accepting bribes to wave through undeclared consignments. Internal VC (Vigilance Commissioner) complaint followed by traps. Both officials caught with ₹4 lakh cash bribe.

**Principal Persons:**
- P0103 — Customs Officer Vijay Kumar (ACCUSED, CONVICTED) — received bribe
- P0104 — Customs Officer Shyam Lal (ACCUSED, CONVICTED) — partner in crime
- P0096 — Priya Sidhu (SUSPECT, PERSON_OF_INTEREST) — suspected intermediary

**Evidence Artifacts:**
- EVD-040-001: Trap report — VC team trap, cash marked with UV powder
- EVD-040-002: CDR — P0103 communications with P0096 in months before trap
- EVD-040-003: Conviction order

**Cross-Case:** CIVIX-036 (P0096 Priya Sidhu connection to gold theft network)

---

## CIVIX-041 | Cross-Border Gold Courier Bust — NH-8 (2024)
**Status:** CLOSED_SOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Gurgaon PS | **Opened:** 2024-05-11

**FIR Narrative:** Road courier intercepted on NH-8 carrying 3.8 kg gold in a false-bottom tiffin carrier. Courier (P0105) admitted receiving the consignment from an Okhla contact for delivery to a Chandni Chowk address. Trail links to both N5 and N2 networks.

**Principal Persons:**
- P0105 — Pappu Courier (real name Rakesh Gupta, ACCUSED, CONVICTED)
- P0025 — Harish Mehta (SUSPECT) — Chandni Chowk recipient (suspected)

**Evidence Artifacts:**
- EVD-041-001: Seizure report — gold in false-bottom tiffin
- EVD-041-002: NH-8 CCTV — vehicle, plate visible
- EVD-041-003: P0105 statement — mentions Chandni Chowk address (matches ORG-031)

**Cross-Case:** CIVIX-010 (ORG-031/Harish Mehta connection), CIVIX-038 (same gold supply chain)

---

## CIVIX-042 | Airport Cargo Smuggling Racket — Okhla (2019)
**Status:** CLOSED_SOLVED | **Priority:** MEDIUM | **Type:** CRIMINAL
**Jurisdiction:** Okhla Industrial Area PS | **Opened:** 2019-10-20

**FIR Narrative:** Large-scale racket using ORG-043 (a legitimate-looking export-import firm) as cover for gold smuggling. Three directors convicted. ₹8.4 crore in undeclared gold seized over the investigation period.

**Principal Persons:**
- P0106, P0107, P0108 — Three ORG-043 Directors (ACCUSED, CONVICTED)

**Evidence Artifacts:**
- EVD-042-001: Customs investigation report
- EVD-042-002: Conviction orders (3)

---

## CIVIX-043 | Gold Concealment in Textile Bales — IGI (2023)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** IGI Airport Cargo PS | **Opened:** 2023-08-17

**FIR Narrative:** 7.1 kg gold concealed within cotton textile bales exported to UAE. Discovered by customs during random exam. Export company (ORG-044) has Tariq Hussain (P0095) as ultimate beneficial owner per corporate intelligence analysis.

**Principal Persons:**
- P0095 — Tariq Hussain (SUSPECT) — UBO of export company
- P0109 — Freight Forwarder (SUSPECT, CHARGESHEETED)

**Evidence Artifacts:**
- EVD-043-001: Customs examination report — concealment method (gold in bale core)
- EVD-043-002: Corporate structure analysis — ORG-044 → Tariq Hussain (3 layers)
- EVD-043-003: X-ray scan imagery (illustrative — diagram-style, not photoreal)

**Cross-Case:** CIVIX-036, CIVIX-038 (Tariq Hussain = central node in N5)

---

# NETWORK N6 — REAL ESTATE LAND GRABBING (Cases 044–050)

---

## CIVIX-044 | Gurugram Sector 44 Benami Land Case [HERO-04 endpoint]
**Status:** OPEN | **Priority:** HIGH | **Type:** PROPERTY
**Jurisdiction:** Gurugram PS | **Opened:** 2025-08-30

**FIR Narrative:** 4.2 acres of agricultural land in Gurugram Sector 44 (Khasra 447) found to be registered in the name of Geeta Devi (P0125, daily wage laborer) but controlled by Dinesh Yadav (P0120) — brother of convicted robber Suresh Valmiki. Financial audit shows ₹58 lakh cash investment in the land, with timing matching proceeds from the 2021 NH-48 robbery (CIVIX-003). This case becomes the endpoint of HERO-04's three-hop discovery chain.

**Principal Persons:**
- P0120 — Dinesh Yadav (SUSPECT, BENEFICIAL OWNER) — brother of Suresh Valmiki
- P0121 — Neelam Yadav (SUSPECT) — wife of Dinesh, also in directorship roles
- P0125 — Geeta Devi (ACCUSED — benami holder, cooperating) — registered owner
- P0130 — Ramesh Patwari (PERSON_OF_INTEREST) — Sub-Registrar official

**Key Events:**
- EVENT-180: PROPERTY_MUTATION — Khasra 447 registered in P0125's name, 2022-03-15
- EVENT-181: TRANSACTION — ₹58 lakh cash transferred through Dinesh Yadav's account, 2022-02-28 (3 months after 2021 robbery)

**Evidence Artifacts:**
- EVD-044-001: Property registry — Khasra 447, Gurugram Sec 44
- EVD-044-002: Financial audit — layered transfer from robbery proceeds (EVD-H04-004)
- EVD-044-003: Dinesh Yadav company directorship extract — Yadav Properties Pvt Ltd
- EVD-044-004: Geeta Devi statement (cooperating — signed papers on instruction)
- EVD-044-005: Property valuation report — 4.2 acres, current value ₹3.8 crore

**Investigative Lead:** LEAD-005 — "Financial Transfer: Robbery Proceeds → Yadav Properties → Khasra 447"
score: 0.78, priority: HIGH
discovery_vector: {"vector_type": "FINANCIAL_PROCEEDS_TRACE", "confidence_signals": {"temporal_match_days": 87, "amount_correlation": 0.82}, "source_case_ids": ["CIVIX-003", "CIVIX-009"], "target_case_id": "CIVIX-044"}

**Cross-Case:** CIVIX-003 (robbery proceeds source), CIVIX-009 (Suresh Valmiki arrest chain), CIVIX-046 (Patwari nexus)

---

## CIVIX-045 | Land Grabbing Syndicate — Gurugram Sec 44 (2019)
**Status:** COLD | **Priority:** LOW | **Type:** PROPERTY
**Jurisdiction:** Gurugram PS | **Opened:** 2019-08-15

**FIR Narrative:** Earlier land grabbing case in same sector. Original owners of 12 plots found their land registered to shell companies. Forged power of attorney documents used. Original investigator could not trace the masterminds. Case went cold.

**Principal Persons:**
- P0120 — Dinesh Yadav (SUSPECT — identified retrospectively via CIVIX-044 linkage)
- P0122 — Ajay Agarwal (SUSPECT, ABSCONDING) — document forger

**Evidence Artifacts:**
- EVD-045-001: Forged POA documents — ink analysis confirms post-date forgery
- EVD-045-002: Original owner statements (12 families)

**Cross-Case:** CIVIX-044 (same syndicate, Dinesh Yadav)

---

## CIVIX-046 | Forged Land Registry — Vasant Kunj (2020)
**Status:** ACTIVE | **Priority:** HIGH | **Type:** PROPERTY
**Jurisdiction:** Vasant Kunj PS | **Opened:** 2020-10-14

**FIR Narrative:** A cooperative society (ORG-050) in Vasant Kunj found its 2.1-acre plot registered to a shell developer (ORG-051) via a forged general body resolution. Patwari official P0130 (Ramesh Patwari) processed the mutation. HERO-09 case.

**Principal Persons:**
- P0120 — Dinesh Yadav (SUSPECT) — developer shell controller
- P0130 — Ramesh Patwari (PERSON_OF_INTEREST) — registry official [HERO-09]
- P0123 — Ravi Khanna (SUSPECT) — document preparation

**Key Events:**
- EVENT-190: PROPERTY_MUTATION — fraudulent registry, 2020-08-15, processed by P0130
- EVENT-191: TRANSACTION — P0130 bank account shows ₹8 lakh cash deposit, 2020-08-16 (day after mutation)

**Evidence Artifacts:**
- EVD-046-001: Forged GBR (general body resolution) — ink/paper analysis shows inconsistency
- EVD-046-002: P0130 bank statement — ₹8 lakh cash deposit day after mutation
- EVD-046-003: P0130 statement — claims cash from ancestral property sale
- EVD-046-004: Sale deed (P0130's claimed source) — document exists but dates don't fully align

**Hypotheses:**
- H-046-A: "Ramesh Patwari accepted ₹8 lakh bribe to process fraudulent mutation" (ACTIVE, POSSIBLE)
  - Support: EVD-046-002 (timing), EVD-046-001 (forged docs passed through him)
  - Contradicting: EVD-046-004 (sale deed partially corroborates his story)
- H-046-B: "Ramesh Patwari is a passive victim who was deceived" (ACTIVE, POSSIBLE)
  - These two hypotheses CONTRADICT each other — CIVIX displays both as unresolved

**Cross-Case:** CIVIX-044 (same Dinesh Yadav network), CIVIX-048 (Patwari nexus — HERO-09)

---

## CIVIX-047 | Illegal Colonizer Racket — Gurugram Sec 44 (2024)
**Status:** REOPENED | **Priority:** HIGH | **Type:** PROPERTY
**Jurisdiction:** Gurugram PS | **Opened:** 2024-08-09

**FIR Narrative:** An unauthorized colony of 40 plots carved out of agricultural land in Gurugram Sector 44. Plots sold without approvals or registered titles. Buyers paid ₹15–35 lakh each but received no legal title. Developer identity unclear — shell company layers.

**Principal Persons:**
- P0120 — Dinesh Yadav (SUSPECT, PROBABLE BENEFICIAL OWNER)
- P0124 — Colony Developer "Builder Bhai" (SUSPECT, UNIDENTIFIED)

**Evidence Artifacts:**
- EVD-047-001: Plot sale agreements (sample 5 of 40) — unregistered
- EVD-047-002: Buyer statements — 40 victims
- EVD-047-003: Shell company analysis — developer corporate structure

**Cross-Case:** CIVIX-044, CIVIX-045 (same Sec 44 geography, same suspected network)

---

## CIVIX-048 | Farmhouse Encroachment — Gurugram (2013)
**Status:** COLD | **Priority:** LOW | **Type:** PROPERTY
**Jurisdiction:** Gurugram PS | **Opened:** 2013-12-26

**FIR Narrative:** Historic encroachment case. 8.5 acres of government-notified agricultural land encroached by two brothers. Case went cold after both brothers paid fines. Land later linked to N6 network as assembly point.

**Principal Persons:**
- P0126 — Vimal Yadav (ACCUSED, FINED — now PERSON_OF_INTEREST)
- P0127 — Kamal Yadav (ACCUSED, FINED)

**Cross-Case:** CIVIX-044 (Yadav family land network)

---

## CIVIX-049 | Benami Property — Vasant Kunj (2025)
**Status:** COLD | **Priority:** MEDIUM | **Type:** PROPERTY
**Jurisdiction:** Vasant Kunj PS | **Opened:** 2025-11-24

**FIR Narrative:** IT Department identified a luxury apartment (ORG-052 ownership) as benami property of a known cyber fraud accused (Aakash Verma, P0070 from CIVIX-027). Property value ₹2.4 crore. Aakash Verma denied ownership from prison.

**Principal Persons:**
- P0070 — Aakash Verma (SUSPECT) — beneficial owner (cross-case)
- P0128 — Sunita Verma (PERSON_OF_INTEREST) — wife, registered owner

**Evidence Artifacts:**
- EVD-049-001: IT Department analysis — unexplained investment
- EVD-049-002: Property registration — Sunita Verma
- EVD-049-003: Financial trace — proceeds from CIVIX-027 fraud to property purchase

**Cross-Case:** CIVIX-027 (Aakash Verma same suspect), demonstrating N4→N6 proceeds cross-network

---

## CIVIX-050 | Builder-Buyer Fraud — DLF Phase 3 (2022)
**Status:** CLOSED_SOLVED | **Priority:** MEDIUM | **Type:** PROPERTY
**Jurisdiction:** Gurugram PS | **Opened:** 2022-09-18

**FIR Narrative:** Developer (ORG-053) collected ₹18 crore from 74 buyers for an apartment project that was never built. Developer's directors absconded; money laundered through shell SPVs. Some funds traced to N2 hawala network.

**Principal Persons:**
- P0129 — Developer Director (ACCUSED, ABSCONDING)
- P0025 — Harish Mehta (SUSPECT) — shell SPV controller (cross-case)

**Evidence Artifacts:**
- EVD-050-001: Buyer complaint compilation (74 buyers)
- EVD-050-002: Shell SPV financial trace

**Cross-Case:** CIVIX-011 (Harish Mehta shell company network)

---

# NETWORK N7 — PUBLIC PROCUREMENT CORRUPTION (Cases 051–055)

---

## CIVIX-051 | Ghost Vendor — DND Flyway PWD Contract (2026) [HERO-07]
**Status:** ACTIVE | **Priority:** HIGH | **Type:** FINANCIAL
**Jurisdiction:** DND Flyway Outpost | **Opened:** 2026-05-05

**FIR Narrative:** PWD contract for ₹4.2 crore (road repair, DND Flyway stretch KM 3–7) awarded to Apex Construction Solutions Pvt Ltd (ORG-060). Apex's registered address (A-42, Sadar Bazar) is the same as known hawala shop (ORG-031). Director Manoj Tandon (P0156) found to have no construction experience. Work quality inspection reveals minimal work actually performed (overcharging). CIVIX surfaces address collision alert.

**Principal Persons:**
- P0155 — Subhash Chandra (PERSON_OF_INTEREST) — retired IAS, suspected facilitator
- P0156 — Manoj Tandon (ACCUSED, ARRESTED) — Apex Construction director
- P0025 — Harish Mehta (SUSPECT) — beneficial owner via ORG-031 address collision

**Key Events:**
- EVENT-200: OTHER — PWD contract awarded, 2025-08-15
- EVENT-201: TRANSACTION — ₹4.2 crore disbursed to Apex, 2025-09-01 to 2025-12-31
- EVENT-202: OTHER — Address collision detected by CIVIX, 2026-05-05

**Evidence Artifacts:**
- EVD-051-001: PWD contract award document — Apex Construction, ₹4.2 crore
- EVD-051-002: Company registration — Apex Construction, registered at A-42 Sadar Bazar
- EVD-051-003: ORG-031 (hawala shop) registration — same address A-42 Sadar Bazar
- EVD-051-004: Work quality inspection report — overcharging, minimal actual work
- EVD-051-005: FIR No. 331/2026

**Investigative Lead:** LEAD-031 — "Address Collision: Ghost Vendor / Hawala Co-location"
score: 0.79, priority: HIGH
discovery_vector: {"vector_type": "ENTITY_ADDRESS_COLLISION", "confidence_signals": {"address_exact_match": true, "both_entities_in_civix": true}, "source_case_ids": ["CIVIX-011"], "target_case_id": "CIVIX-051"}

**Cross-Case:** CIVIX-011 (Harish Mehta same network), CIVIX-015 (hawala proceeds to ghost vendor scheme)

---

## CIVIX-052 | Public Tender Manipulation — Connaught Place (2021)
**Status:** OPEN | **Priority:** MEDIUM | **Type:** FINANCIAL
**Jurisdiction:** Connaught Place PS | **Opened:** 2021-04-27

**FIR Narrative:** Whistleblower complaint alleging that NDMC tender evaluation committee pre-shared technical specifications with a specific vendor (ORG-061) to ensure their bid won. ₹7.8 crore water supply contract. Investigation ongoing.

**Principal Persons:**
- P0157 — Reena Saxena (SUSPECT) — NDMC evaluation committee member
- P0160 — ORG-061 Proprietor (PERSON_OF_INTEREST)

**Evidence Artifacts:**
- EVD-052-001: Whistleblower complaint
- EVD-052-002: Tender document — technical specs matching ORG-061's proprietary system
- EVD-052-003: CDR — P0157 phone contact with ORG-061 proprietor 2 weeks before tender

---

## CIVIX-053 | Bribery in Contract Award — ITO PWD (2023)
**Status:** CLOSED_SOLVED | **Priority:** HIGH | **Type:** CRIMINAL
**Jurisdiction:** ITO / Central Delhi PS | **Opened:** 2023-04-22

**FIR Narrative:** PWD official at ITO (P0158 Satish Gupta) caught accepting ₹12 lakh bribe for steering a contract to a favored vendor. CBI trap operation. Both parties convicted.

**Principal Persons:**
- P0158 — Satish Gupta, PWD Engineer (ACCUSED, CONVICTED)
- P0161 — Contractor Naresh Mehra (ACCUSED, CONVICTED)

**Evidence Artifacts:**
- EVD-053-001: CBI trap report — marked currency
- EVD-053-002: Conviction order
- EVD-053-003: CDR — P0158/P0161 call pattern in months before bribe

---

## CIVIX-054 | Corporate Kickback — Delhi Secretariat (2019)
**Status:** REOPENED | **Priority:** HIGH | **Type:** FINANCIAL
**Jurisdiction:** ITO / Central Delhi PS | **Opened:** 2019-08-18

**FIR Narrative:** Kickback scheme involving a Delhi Secretariat official facilitating land-use conversion approvals for real estate developers. 14 conversions suspected, ₹2.4 crore in kickbacks. Original case partially closed. Reopened when financial analysis in CIVIX-044 surfaced a matching payment trail.

**Principal Persons:**
- P0155 — Subhash Chandra (SUSPECT) — retired IAS, connected to approvals
- P0162 — Developer Group (multiple, SUSPECTS)

**Evidence Artifacts:**
- EVD-054-001: Land-use conversion orders — 14 orders, all facilitated by P0155's department
- EVD-054-002: Financial trail — payments to shell entities connected to P0155

**Cross-Case:** CIVIX-044 (land use for Dinesh Yadav land), CIVIX-051 (Subhash Chandra same nexus)

---

## CIVIX-055 | Inflated Billing — DND Flyway Maintenance (2020)
**Status:** ACTIVE | **Priority:** MEDIUM | **Type:** FINANCIAL
**Jurisdiction:** DND Flyway Outpost | **Opened:** 2020-04-10

**FIR Narrative:** Annual DND Flyway maintenance contract billed at 340% of actual work done. Contractor (ORG-065) and supervising engineer (P0163) found to have colluded. Investigation ongoing; engineer suspended, contractor chargesheeted.

**Principal Persons:**
- P0163 — PWD Supervising Engineer (ACCUSED, SUSPENDED)
- P0164 — ORG-065 Contractor (ACCUSED, CHARGESHEETED)

**Evidence Artifacts:**
- EVD-055-001: Quantity surveyor report — actual vs. billed work discrepancy
- EVD-055-002: Bank statement — ORG-065 payments to P0163's family members

**Cross-Case:** CIVIX-051 (same DND corridor, suspected N7 network pattern)

# CIVIX 2.0 — PRESENTATION INVESTIGATION UNIVERSE BIBLE
## Version 4.0 | 55-Case Deep Universe | Delhi NCR Criminal Ecosystem
### Classification: DEMO SEED DATA — ALL PERSONS, CASES, EVENTS ARE ENTIRELY FICTIONAL

---

# SECTION 1 — UNIVERSE OVERVIEW & DESIGN PHILOSOPHY

## 1.1 What This Universe Is

This is not a test dataset. It is a synthetic criminal intelligence world — a living, breathing Delhi NCR investigative ecosystem where the same people, phones, vehicles, bank accounts, and aliases resurface across unrelated cases the way they do in real multi-agency investigations.

Every case has depth: an FIR narrative, witnesses who contradict each other, forensic evidence that partially confirms a hypothesis, financial trails that branch into dead ends, and suspects whose mobile behavior produces meaningful XGBoost signals. Some cases are closed and wrong. Some leads are real. Some are carefully constructed false positives.

The universe's purpose is to make CIVIX's core value proposition immediately legible to a judge in a 15-minute live demo: **multi-hop cross-case discovery that no single investigator could manually perform**.

## 1.2 Core Design Principles

**P1 — Depth over width.** Every case has a minimum of: 1 FIR narrative, 3 principal suspects/persons of interest with full dossiers, 5 events in the event timeline, 3 evidence artifacts, 1 hypothesis with supporting/contradicting evidence, and 1 cross-case relationship.

**P2 — Ground truth is hidden.** The interesting connections are never stated explicitly in any single case file. CIVIX must derive them from the underlying evidence graph.

**P3 — False positives are first-class citizens.** For every 3 true cross-case connections there is 1 deliberately misleading correlation that CIVIX must correctly flag as low-confidence.

**P4 — Identity ambiguity is real.** At least 15 persons have unresolved identity candidates. Common names create noise. Operational aliases create signal.

**P5 — Schema compliance is absolute.** No invented tables, columns, or enums. Every field maps to the verified 63-table CIVIX schema contract v3.0.0.

**P6 — Face matching is a stub.** Vehicle/ANPR evidence carries cross-case spatial weight. Facial recognition is referenced as "pending manual verification" only.

**P7 — XGBoost signals are signals, not facts.** Behavioral profiles are designed to produce meaningful variation — high-signal suspects, moderate-signal innocents, suspicious-looking but irrelevant bystanders.

## 1.3 Universe Scale Targets

| Entity Type | Count | Notes |
|---|---|---|
| Cases | 55 | 7 networks + 3 standalone |
| Principal Persons (full dossiers) | 320 | Named, alibied, behavioral profiles |
| Background Persons | 85 | Named, minimal detail, appear in 1–2 events |
| Organizations | 95 | Shell cos, hawala, logistics, real cos |
| Vehicles | 160 | Including cloned plates, chop-shop chains |
| Phone Numbers (MSISDN) | 380 | Including burners, shared handsets |
| SIM Cards | 380 | 1:1 with phone numbers |
| Devices (IMEI) | 195 | Some shared across SIMs |
| Financial Accounts | 110 | Bank, wallet, shell corporate |
| Properties | 45 | Residential, commercial, agricultural |
| Locations (PostGIS) | 140 | Crime scenes, towers, CCTV coverage zones |
| Events | 680+ | Calls, transactions, sightings, arrests |
| Evidence Artifacts | 420+ | FIRs, CDRs, ANPR crops, forensic reports |
| Investigative Leads | 45 | AI-surfaced, scored, with discovery vectors |
| Hypotheses | 88 | With supporting/contradicting evidence |
| Assertions | 210 | Subject-predicate-object, epistemic status |
| Identity Candidates | 28 | Mix of resolved/unresolved/rejected |
| Hero Cases | 12 | Full demo narrative defined |

---

# SECTION 2 — DELHI NCR GEOGRAPHY & SPATIAL ARCHITECTURE

## 2.1 Operational Corridors

The universe operates across eight spatial corridors, each hosting distinct criminal infrastructure:

**CORRIDOR A — Dwarka / NH-48 / Najafgarh (Robbery & Logistics)**
- Crime scenes: Dwarka Sector 23 cash point, NH-48 KM 14, Najafgarh Mandi Road
- Key locations: Dwarka PS, NH-48 Toll Plaza (28.5726°N, 77.0555°E), Najafgarh Bus Terminal
- CCTV coverage: CAM-01 (Dwarka Sector 23 T-Junction), CAM-02 (NH-48 Toll A), CAM-03 (NH-48 Toll B), CAM-04 (Najafgarh Main Market)
- Cell towers: TOWER-DW-01 (Dwarka Sec 23), TOWER-NH-01 (NH-48), TOWER-NJ-01 (Najafgarh)

**CORRIDOR B — Chandni Chowk / Sadar Bazar / Karol Bagh (Hawala)**
- Key locations: Chandni Chowk Bullion Market, Sadar Bazar Money Lane, Karol Bagh trade center
- CCTV: CAM-05 (Chandni Chowk main), CAM-06 (Sadar Bazar entry), CAM-07 (Karol Bagh Ajmal Khan Road)
- Cell towers: TOWER-CC-01 (Chandni Chowk), TOWER-SB-01 (Sadar Bazar), TOWER-KB-01 (Karol Bagh)

**CORRIDOR C — Karol Bagh / Mayapuri / Tilak Nagar (Vehicle Theft)**
- Key locations: Mayapuri chop-shop industrial cluster, Tilak Nagar vehicle market, Karol Bagh spare parts row
- CCTV: CAM-08 (Mayapuri Phase 2 Gate), CAM-09 (Tilak Nagar crossing), CAM-10 (Karol Bagh spare parts)
- Cell towers: TOWER-MY-01 (Mayapuri), TOWER-TN-01 (Tilak Nagar)

**CORRIDOR D — Rohini / Outer Delhi / Bawana (Cyber Fraud)**
- Key locations: Rohini Sector 16 call center cluster, Bawana Industrial Area warehouses
- CCTV: CAM-11 (Rohini Sector 16 Metro exit), CAM-12 (Bawana Industrial Gate)
- Cell towers: TOWER-RH-01 (Rohini Sector 16), TOWER-RH-02 (Rohini Sector 22), TOWER-BW-01 (Bawana)

**CORRIDOR E — IGI Airport / Okhla / Nizamuddin (Smuggling)**
- Key locations: IGI Cargo Terminal Gate 3, Okhla Industrial Area Phase 1, Nizamuddin Railway Station
- CCTV: CAM-13 (IGI Cargo gate), CAM-14 (Okhla Phase 1 main), CAM-15 (Nizamuddin approach road)
- Cell towers: TOWER-IGI-01 (Airport cargo), TOWER-OK-01 (Okhla), TOWER-NZ-01 (Nizamuddin)

**CORRIDOR F — Gurugram / DLF / Sohna Road (Real Estate)**
- Key locations: Gurugram Sector 44 land parcels, DLF Phase 3 registry office, Sohna Road development sites
- CCTV: CAM-16 (Gurugram Sector 44 entry), CAM-17 (DLF Phase 3 gate), CAM-18 (Sohna Road checkpoint)
- Cell towers: TOWER-GG-01 (Gurugram Sec 44), TOWER-GG-02 (Sohna Road)

**CORRIDOR G — ITO / Connaught Place / DND Flyway (Corruption)**
- Key locations: ITO PWD office, Connaught Place Inner Circle, DND Flyway Toll, Delhi Secretariat
- CCTV: CAM-19 (ITO crossing), CAM-20 (CP Inner Circle), CAM-21 (DND Toll), CAM-22 (Delhi Secretariat gate)
- Cell towers: TOWER-ITO-01 (ITO), TOWER-CP-01 (Connaught Place), TOWER-DND-01 (DND Flyway)

**CORRIDOR H — Noida / Greater Noida / Ghaziabad (Cyber + Overflow)**
- Key locations: Noida Sector 62 IT park, Greater Noida call center cluster, NH-58 corridor
- CCTV: CAM-23 (Noida Sector 62 gate), CAM-24 (Greater Noida Expressway toll), CAM-25 (NH-58 Ghaziabad check post)
- Cell towers: TOWER-NO-01 (Noida Sec 62), TOWER-GN-01 (Greater Noida), TOWER-GZ-01 (Ghaziabad)

## 2.2 Network Interlocks — Spatial

```
NH-48 / Dwarka [N1] ─────── VEHICLE SUPPLY ──────► Mayapuri/Karol Bagh [N3]
         │                                                    │
         │ CASH WASHING                            UNTRACEABLE VEHICLES
         ▼                                                    ▼
Chandni Chowk / Sadar Bazar [N2] ◄──── PROCEEDS ──── IGI Cargo / Okhla [N5]
         │                                                    
         │ SHELL COMPANY INVESTMENT                          
         ▼                                                    
Gurugram / DLF [N6] ◄───────────────── LAND INVESTMENT ──── Rohini/GN [N4]
         │
         │ LAND-USE CONVERSION BRIBERY
         ▼
ITO / CP [N7]
```

---

# SECTION 3 — INVESTIGATIVE NETWORK ARCHITECTURE

## Network N1 — Armed Robbery & Cash-in-Transit Syndicate
**Operational Area:** Dwarka, NH-48, Najafgarh, Uttam Nagar
**Active Period:** 2011–2026 (multi-generational gang)
**Core MO:** Surveillance of cash-van schedules via insider tip (often ex-security guard), coordinated interception with 3–6 persons, motorcycle outriders, getaway vehicle rotation
**Funding Downstream:** Cash laundered via N2 hawala operators in Sadar Bazar; vehicles sourced from N3 Mayapuri chop-shop
**Cases:** CIVIX-001 through CIVIX-009 (9 cases)
**Principal Leader:** Suresh Valmiki aka "Suri Bhai" (P0001)
**Key Associates:** Rakesh Yadav (P0002), Mohinder Bhati (P0003), Ramesh Chauhan (P0004), Devender Nagar (P0005)

## Network N2 — Hawala & Financial Shell Company Fraud
**Operational Area:** Chandni Chowk, Sadar Bazar, Karol Bagh, Noida Sector 62
**Active Period:** 2013–2026
**Core MO:** GST-registered shell companies (fake invoicing), hawala network using bullion traders as cover, SAR suppression via bank insider, round-tripping funds through real estate SPVs
**Cases:** CIVIX-010 through CIVIX-018 (9 cases)
**Principal Leader:** Harish Mehta aka "Seth-ji" (P0020)
**Key Associates:** Priya Malhotra (P0021), Salim Sheikh (P0022), Vikram Arora (P0023)

## Network N3 — Luxury Vehicle Theft & Plate Cloning Ring
**Operational Area:** Karol Bagh, Mayapuri, Tilak Nagar, NH-48
**Active Period:** 2019–2026
**Core MO:** High-end vehicle theft from parking lots, VIN stamping in Mayapuri chop-shops, plate cloning for courier/getaway use, RC forgery through corrupt RTO agent
**Cases:** CIVIX-019 through CIVIX-026 (8 cases)
**Principal Leader:** Joginder "Jogi" Kalra (P0045)
**Key Associates:** Pawan Sharma (P0046), Deepak Tyagi (P0047), Mithun Das (P0048)

## Network N4 — Cyber Extortion & Digital Arrest Fraud
**Operational Area:** Rohini, Greater Noida, Bawana, Ghaziabad
**Active Period:** 2020–2026
**Core MO:** "Digital arrest" scam — impersonating CBI/ED/Narcotics officers, demanding cash to "close fake FIRs", sextortion via fake profiles, KYC phishing, coordinated OTP fraud
**Cases:** CIVIX-027 through CIVIX-035 (9 cases)
**Principal Leader:** Aakash Verma aka "AV Sir" (P0070)
**Key Associates:** Nitesh Goyal (P0071), Sonia Rathore (P0072), Farrukh Tashkentov (P0073)

## Network N5 — Contraband & Gold Smuggling
**Operational Area:** IGI Airport Cargo, Okhla, Nizamuddin, NH-8
**Active Period:** 2015–2026
**Core MO:** Gold concealment in cargo consignments (machinery, textile bales), corrupt customs clearing agent, road courier network from Mumbai/Kolkata, Hawala settlement with N2
**Cases:** CIVIX-036 through CIVIX-043 (8 cases)
**Principal Leader:** Tariq Hussain aka "Sona Bhai" (P0095)
**Key Associates:** Priya Sidhu (P0096), Joseph Fernandez (P0097), Meena Nair (P0098)

## Network N6 — Real Estate Land Grabbing Syndicate
**Operational Area:** Gurugram, Vasant Kunj, Saket, Faridabad
**Active Period:** 2018–2026
**Core MO:** Forged power of attorney documents, Benami ownership through relatives, builder-buyer fraud, nexus with corrupt Patwari/registry officials, intimidation of original owners
**Cases:** CIVIX-044 through CIVIX-050 (7 cases)
**Principal Leader:** Dinesh Yadav (P0120)
**Key Associates:** Neelam Yadav (P0121), Ajay Agarwal (P0122), Ravi Khanna (P0123)

## Network N7 — Public Procurement Corruption Ring
**Operational Area:** ITO, Connaught Place, Delhi Secretariat, PWD offices
**Active Period:** 2016–2026
**Core MO:** Tender rigging through inside information, shell vendor registration, kickback routing via N2 shell companies, bureaucrat-builder nexus, forged completion certificates
**Cases:** CIVIX-051 through CIVIX-055 (5 cases)
**Principal Leader:** Subhash Chandra IAS (retd.) (P0155)
**Key Associates:** Manoj Tandon (P0156), Reena Saxena (P0157), Satish Gupta (P0158)

---

# SECTION 4 — HERO CASE DEFINITIONS (12 HERO INVESTIGATIONS)

## HERO-01: "The Fifth Robber" — CIVIX-001
**Demo Narrative Arc:** Cold case → Identity candidate → Cross-case alias match → Lead generated

**Case:** Dwarka Sector 23 Cash Van Robbery, March 2012. Five armed suspects intercept an SBI cash van at the Sector 23 T-junction at 07:43. Guards overpowered, ₹47 lakh seized. Four suspects arrested within 72 hours (P0002, P0003, P0004, P0005). The fifth suspect — seen on CAM-01 CCTV wearing a grey tracksuit, face partially obscured — escapes. Case status: CLOSED_SOLVED (four convicted), but PERSON_UNKNOWN_05 remains at large.

**The Hidden Connection:** In CIVIX-028 (Rohini Digital Arrest Ring, 2021), an interrogation transcript of suspect Nitesh Goyal (P0071) mentions his recruiter as "Vikram @ Pandit" — a handle that appears nowhere in CIVIX-001's official record. However, buried in the interrogation transcript of CIVIX-001 convict Rakesh Yadav (P0002), a 2013 prison statement references "the one who planned the vehicle approach — we called him Pandit." The grey tracksuit figure's height estimate (5'9"–5'11") matches. Additionally, a burner phone (T0011) that pinged TOWER-DW-01 at 07:38 on the robbery morning (4 minutes before the incident) pinged TOWER-RH-01 eighteen months later during a fraud call linked to CIVIX-028.

**CIVIX Discovery Chain:**
1. Analyst queries CIVIX-001 for PERSON_UNKNOWN_05
2. System surfaces identity candidate IC-001: alias "Vikram @ Pandit" appearing in two separate case transcripts
3. Graph traversal shows T0011 as the connecting node (CIVIX-001 tower ping ↔ CIVIX-028 CDR)
4. Lead LEAD-001 generated: "Alias-Device Overlap — CIVIX-001/CIVIX-028" score 0.87, priority HIGH

**Ground Truth:** TRUE POSITIVE. Vikram Sharma aka "Vikram @ Pandit" (P0075) is Person Unknown 05. He later joined the N4 cyber fraud network. The alias and device overlap are both valid signals.

**Evidence Assets Required:**
- EVD-H01-001: CAM-01 CCTV still (grey tracksuit figure, 07:43:12, partially obscured)
- EVD-H01-002: CIVIX-001 FIR document (handwritten, Delhi Police format)
- EVD-H01-003: Interrogation transcript — Rakesh Yadav 2013 prison statement mentioning "Pandit"
- EVD-H01-004: CDR dump for T0011 showing TOWER-DW-01 ping 2012-03-14 07:38
- EVD-H01-005: Interrogation transcript — Nitesh Goyal 2021 mentioning "Vikram @ Pandit"
- EVD-H01-006: CDR dump for T0011 showing TOWER-RH-01 pings 2021

**Capabilities Demonstrated:** Case workspace, evidence explorer, graph traversal, alias identity candidate, event timeline, CDR communications, investigative lead

---

## HERO-02: "The Reopened Gold Case" — CIVIX-036 + CIVIX-010
**Demo Narrative Arc:** Closed cold case → Bank SAR → Shell company → Automatic REOPENED

**Case:** Nizamuddin Gold Bar Theft, June 2018. ₹2.3 crore in gold bars stolen from a bullion courier at Nizamuddin Railway Station. Prime suspect: Tariq Hussain (P0095), customs clearing agent. Case investigated, insufficient evidence to charge Tariq — case closed CLOSED_UNSOLVED.

**The Hidden Connection:** In February 2026, CIVIX-010 (Shell Company GST Fraud investigation) generates a Bank SAR from HDFC Karol Bagh branch flagging suspicious credits to "Arham Bullion Traders Pvt Ltd." CIVIX ingests the SAR. The NER extraction pipeline pulls the GST number from the SAR document: 07AARCA1234J1Z1. When CIVIX checks this GST number against existing case entities, it finds an exact match — the same GST number appears in Tariq Hussain's company registration documents scanned into CIVIX-036 in 2018. The director's PAN (AARCA1234J) is identical. Tariq's address in 2018 (Nizamuddin West, House 47) matches the registered address of Arham Bullion Traders.

**CIVIX Discovery Chain:**
1. Bank SAR ingested as evidence_artifact in CIVIX-010
2. Extraction pipeline (extraction_type = NER) pulls GST number from SAR PDF
3. Assertion created: SOURCE_IDENTITY(GST:07AARCA1234J1Z1) REGISTERED_AT ORGANIZATION(Arham Bullion Traders)
4. Graph query finds identical GST in CIVIX-036 entity records → match candidate
5. Lead LEAD-002 generated: "GST Registration Overlap — Cold Case Linkage" score 0.94, priority CRITICAL
6. Case status recommendation: CIVIX-036 CLOSED_UNSOLVED → REOPENED (investigator must approve)

**Ground Truth:** TRUE POSITIVE. Tariq Hussain laundered the 2018 theft proceeds through Arham Bullion Traders, which he registered under a relative's name but his own GST number.

**Evidence Assets Required:**
- EVD-H02-001: Bank SAR PDF — HDFC Karol Bagh, flagging Arham Bullion Traders
- EVD-H02-002: CIVIX-036 original FIR (Nizamuddin PS, 2018)
- EVD-H02-003: Tariq Hussain's company registration documents (GST cert, director PAN)
- EVD-H02-004: Arham Bullion Traders GST registration certificate (same number, 2024)
- EVD-H02-005: Financial transaction extract — Arham Bullion Traders account credits

**Capabilities Demonstrated:** SAR ingestion, NER extraction, assertion creation, graph lookup, case status auto-flag, identity resolution

---

## HERO-03: "The Spatial Paradox" — CIVIX-019
**Demo Narrative Arc:** ANPR event → Spatial impossibility → Vehicle clone → Ring identified

**Case:** Plate cloning investigation. Black Toyota Fortuner, plate DL-8C-AB-1234.

**The Event Sequence:**
- 2026-04-03, 14:22:07 — CAM-02 (NH-48 Toll A, Dwarka, approx. 28.5726°N 77.0555°E): ANPR reads DL-8C-AB-1234, direction OUTBOUND toward Gurugram
- 2026-04-03, 14:24:51 — CAM-15 (Nizamuddin approach, approx. 28.5918°N 77.2442°E): ANPR reads DL-8C-AB-1234, direction INBOUND toward Delhi

**The Impossibility:** 14.7 km in 2 minutes 44 seconds = 321 km/h. PostGIS `ST_Distance` query confirms 14,720 meters between the two camera locations. The `data_quality_issue` table flags: `SPATIAL_IMPOSSIBILITY`.

**CIVIX Discovery Chain:**
1. Batch ANPR processing detects the temporal-spatial impossibility
2. DQ issue created: type SPATIAL_IMPOSSIBILITY, entities [V0001, CAM-02, CAM-15]
3. Investigative Lead LEAD-003 generated: "ANPR Spatial Paradox — Vehicle Cloning Probable" score 0.95, priority CRITICAL
4. Graph traversal: V0001 (DL-8C-AB-1234) → registered owner Ravi Malhotra (P0050) → linked to Mayapuri chop-shop address → CIVIX-022 (Engine re-stamping case)
5. CIVIX queries all ANPR events for DL-8C-AB-1234 → 14 sightings across 6 months, 3 more impossible pairs
6. VIN from Toll Plaza RFID: two different VINs logged against same plate → confirmed two physical vehicles

**Ground Truth:** TRUE POSITIVE. Two Fortuners bearing DL-8C-AB-1234. Original owned by Ravi Malhotra (legitimate). Clone operated by Pawan Sharma (P0046) for getaway/courier use.

**Evidence Assets Required:**
- EVD-H03-001: ANPR crop — CAM-02 DL-8C-AB-1234, 14:22:07 (plate clearly visible, front angle)
- EVD-H03-002: ANPR crop — CAM-15 DL-8C-AB-1234, 14:24:51 (plate visible, different lighting)
- EVD-H03-003: PostGIS spatial analysis map output (two points, distance annotation)
- EVD-H03-004: Vehicle registration certificate — DL-8C-AB-1234 (Ravi Malhotra, legitimate)
- EVD-H03-005: CIVIX ANPR timeline — all 14 sightings chart

**Capabilities Demonstrated:** ANPR pipeline, spatial impossibility detection, data quality issue, graph traversal, multi-event correlation

---

## HERO-04: "Three-Hop Discovery" — CIVIX-009 → CIVIX-003 → CIVIX-044
**Demo Narrative Arc:** Fresh arrest → Biometric hit → Cold case reopened → Second active case surfaces

**Case Chain:**
- HOP-0: Suresh Valmiki (P0001) arrested 2026-07-19, CIVIX-009 (Najafgarh robbery)
- HOP-1: AFIS ten-print booking matches latent print from CIVIX-003 (NH-48 Dacoity 2021, COLD) — cold case auto-flagged for reopening
- HOP-2: Graph expands from P0001 → brother Dinesh Yadav (P0120) → shell company director → Benami land parcel → CIVIX-044 (OPEN, Gurugram land fraud)

**Evidence Assets Required:**
- EVD-H04-001: AFIS booking card — Suresh Valmiki ten prints, 2026-07-19
- EVD-H04-002: Latent print AFIS card — NH-48 getaway vehicle steering wheel, 2021 (now matched)
- EVD-H04-003: Company directorship extract — Yadav Properties Pvt Ltd, showing Dinesh Yadav
- EVD-H04-004: Financial audit — layered transfer from robbery proceeds to land SPV

---

## HERO-05: "The Shared Handset" — CIVIX-027 + CIVIX-019
**Demo Narrative Arc:** Two cases, one IMEI, two different SIMs, identity candidate surfaced

A Samsung Galaxy A-series handset (IMEI: 357891049234561) is used with two different SIMs 8 months apart. First SIM (T0045) appears in CIVIX-027 (KYC phishing ring, Shahdara). Second SIM (T0091) appears in CIVIX-019 (Fake RC registration, Karol Bagh). Neither case knows about the other. CIVIX's device-SIM junction table surfaces the overlap. Identity candidate IC-007 is created between the two SIM users.

**Ground Truth:** PROBABLE. The handset was sold secondhand between the two users. Ground truth is ambiguous — it may be a legitimate resale rather than the same criminal. CIVIX correctly surfaces this as a candidate, NOT a confirmed link.

---

## HERO-06: "The Common Notary" — False Positive Demo
**Demo Narrative Arc:** Same witness name → Appears to link 3 cases → Actually a legitimate professional

Ratan Lal Sharma, a professional notary (P0200), witnesses documents in CIVIX-044, CIVIX-047, and CIVIX-050. His name appears in three land dispute cases. Naive graph analysis would make him a central node. CIVIX's epistemic layer correctly scores this IC-015 at 0.23 confidence (LOW), notes his professional role, and does NOT generate a lead. The demo shows the investigator hovering over the low-confidence node and seeing the explicit reasoning: "Subject is a registered notary; document witnessing is their professional function. Spatial and temporal overlap is explained by professional role. No further action recommended."

**Ground Truth:** FALSE POSITIVE. Ratan Lal Sharma is a legitimate notary with no criminal involvement.

---

## HERO-07: "The Ghost Vendor" — CIVIX-051
**Demo Narrative Arc:** Procurement fraud → Shell vendor → Same director → Cross-network financial wash

PWD contract awarded to "Apex Construction Solutions Pvt Ltd" for ₹4.2 crore (road repair, DND Flyway stretch). Apex's director is Manoj Tandon (P0156). However, Apex's registered address (A-42, Sadar Bazar) is the same as a known hawala shop (ORG-031, Sadar Bazar Money Exchange). CIVIX surfaces assertion: ORGANIZATION(Apex Construction) REGISTERED_AT LOCATION(A-42 Sadar Bazar) which is also LOCATED_AT the same geometry as ORG-031. Lead LEAD-031: "Address Collision — Ghost Vendor / Hawala Co-Location" score 0.79.

---

## HERO-08: "The Cloned SIM Trail" — CIVIX-032 + CIVIX-014
**Demo Narrative Arc:** SIM ownership chain → Person used two networks of phones → behavioral model flags

Farrukh Tashkentov (P0073) — originally from Uzbekistan, overstayed visa — is the operational coordinator for CIVIX-032 (Digital Arrest call center). His ICCID (SIM-0073) is registered to a legitimate-seeming business. However, CDR analysis shows 847 calls in 30 days, 73% between 23:00 and 04:00, contact concentration 0.91 (top 3 contacts = 91% of all calls). XGBoost behavioral model scores this profile 0.84 (HIGH behavioral anomaly). The demo shows the XGBoost feature importance panel.

---

## HERO-09: "The Patwari Nexus" — CIVIX-044 + CIVIX-046
**Demo Narrative Arc:** Two land cases → Same registry official → Property mutation events → Corruption hypothesis

Ramesh Patwari (P0130), a revenue official at Gurugram Sub-Registrar office, appears as REGISTRAR in property mutation events in both CIVIX-044 (Benami land case) and CIVIX-046 (Illegal colonizer). Assertion: PERSON(Ramesh Patwari) REGISTERED_AT PROPERTY(Khasra 447, Gurugram Sec 44) AND PROPERTY(Plot B-7, Sohna Road). Hypothesis H-041: "Ramesh Patwari accepted bribes to facilitate fraudulent mutations." Evidence support: EVD-H09-001 (bank statement showing ₹8 lakh cash deposits on dates matching both mutations). Contradicting evidence: EVD-H09-002 (Patwari's statement that cash was ancestral property sale proceeds — documented with sale deed).

**CIVIX Shows:** Competing hypothesis support/contradiction. Epistemic status = POSSIBLE, not CONFIRMED.

---

## HERO-10: "The Interpol Overlap" — CIVIX-038 (Border Crossing)
**Demo Narrative Arc:** Airport CDR → Border crossing event → Cross-network financier identified

Mohammed Irfan Qureshi (P0100), who appears as a minor character in CIVIX-038 (IGI cargo smuggling), has a BORDER_CROSSING event recorded at Wagah (2024-11-15, outbound to Pakistan). His financial account (ACC-0100) shows ₹14 lakh transferred to a Dubai-based intermediary 3 days before the crossing. CIVIX surfaces Lead LEAD-038: "Pre-departure Large Transfer + Border Crossing — Financial Flight Risk" score 0.71, priority HIGH.

---

## HERO-11: "The Common Vehicle Corridor" — CIVIX-003 + CIVIX-022
**Demo Narrative Arc:** Vehicle seen at two crime scenes, different cases, different years

Mahindra Bolero, HR-06UH-3818 (V0005), is observed at:
- CIVIX-003 (NH-48 Dacoity 2021): CAM-02 footage shows a dark Bolero parked 80m from incident 11 minutes before
- CIVIX-022 (Gold bar concealment 2025): Okhla CCTV shows same plate loading consignment boxes

Neither investigating officer searched for cross-case vehicle overlap. CIVIX's vehicle-sighting event table surfaces the overlap automatically. Lead LEAD-022: "Vehicle Cross-Case Sighting" score 0.67, priority MEDIUM. Ground truth: PROBABLE — same vehicle, different modules of the same smuggling supply chain.

---

## HERO-12: "The Linguistics Trap" — False Positive Demo 2
**Demo Narrative Arc:** Alias overlap → Different people → CIVIX declines to merge

"Bhura" appears as an alias for:
- P0003 — Mohinder Bhati aka "Bhura" (N1 robbery gang member)
- P0133 — Harpal Singh aka "Bhura" (legitimate truck driver, appears as witness in CIVIX-041)

CIVIX creates identity candidate IC-022, score 0.31 (LOW). The alias is phonetically identical but the underlying persons have different DOBs, Aadhaar numbers, home areas, and physical descriptions. CIVIX does NOT auto-resolve this. The demo shows an investigator opening IC-022 and seeing the explicit conflict signals that prevent automatic merge.

**Ground Truth:** FALSE POSITIVE. Common nickname. Different people.

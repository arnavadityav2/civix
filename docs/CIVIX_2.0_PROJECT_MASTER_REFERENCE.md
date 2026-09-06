# CIVIX 2.0 — Project Master Reference Document

**Document Status**: Authoritative Project Master Reference & Workstation Blueprint  
**Audience**: Senior Engineering Leadership, SIH Evaluators, System Architects, Lead Investigators  
**Authority Rule**: Derived directly from `docs/00_CIVIX_CURRENT_STATE.md` and repository code inspection.

---

## 1. Executive Summary & Core Mission

CIVIX 2.0 is a state-of-the-art **Investigative Intelligence Workstation** engineered to solve the critical challenge of **fragmented, multi-modal investigative data** in complex law enforcement, counter-fraud, and intelligence operations.

In modern criminal investigations, data arrives in disconnected, heterogeneous silos:
- **Telecom Records**: Call Detail Records (CDRs), IP Detail Records (IPDRs), IMEI/IMSI pairing logs, cell tower coverage maps.
- **Financial Networks**: Bank ledger transactions, UPI transfers, credit card logs, high-value cash deposits, shell account networks.
- **Computer Vision & Video**: CCTV video feeds, Automated License Plate Recognition (ANPR), SORT vehicle tracking logs, facial embeddings.
- **Geospatial Telemetry**: Cell tower GIS centroids, vehicle movement vectors, PostGIS location points, spatiotemporal co-location events.
- **Unstructured Intelligence**: Witness statements, PDF FIR reports, police case diaries, forensic reports, uploaded evidence vaults.

CIVIX 2.0 unifies these fragmented data points into a single, cohesive, **evidence-backed, security-enforced investigative workstation**. It bridges relational transactions with graph-oriented multi-hop link analysis while strictly maintaining **epistemic provenance**, **Row-Level Security (RLS)**, and **bitemporal court admissibility**.

---

## 2. Complete Technology Stack Inventory

| Component Layer | Technology / Framework | Version / Package | Purpose & Implementation Details |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React 18 (TypeScript), Vite 5 | React 18.2, Vite 5.0 | High-performance Single Page Application (SPA) with strict type safety, modular routing, and reactive state management. |
| **Graph Visualization Engine** | Cytoscape.js | `cytoscape` 3.28, `cytoscape-fcose` | Hardware-accelerated canvas/SVG multi-hop graph rendering, fCoSE layout physics, dynamic node clustering, and edge filtering. |
| **GIS & Spatial Mapping** | Leaflet, React-Leaflet | Leaflet 1.9, OpenStreetMap | Interactive GIS map canvas rendering PostGIS spatial centroids, cell tower radii, vehicle trajectory vectors, and spatiotemporal timeline scrubbing. |
| **UI Component System** | TailwindCSS, Lucide Icons | Tailwind 3.4, Lucide React | Modern dark-mode glassmorphic user interface, high-contrast visual cues, responsive grid layouts, and custom CSS variables. |
| **Asynchronous API Server** | Python 3.12, FastAPI | FastAPI 0.109, Uvicorn 0.27 | Asynchronous REST API server handling JWT authentication, request validation (Pydantic v2), OpenAPI documentation, and route dispatching. |
| **Primary System of Record** | PostgreSQL 16 + PostGIS | PostgreSQL 16.1, PostGIS 3.4 | Authoritative transactional data store, bitemporal schema triggers, strict Row-Level Security (RLS), and PostGIS spatial indexing (`GEOMETRY`). |
| **Graph Database Projection** | Neo4j 5 Enterprise / Community | Neo4j 5.15, Cypher 5 | Read-optimized multi-hop graph traversal engine executing 1–5 hop Cypher queries, path analysis, and graph centrality calculations. |
| **CDC / Event Synchronization** | PostgreSQL Outbox + Async Python Worker | Transactional Outbox Pattern | Asynchronous, idempotent event synchronization queue (`civix.outbox`) ensuring PostgreSQL mutations project to Neo4j without distributed transactions. |
| **Behavioral Anomaly ML** | XGBoost 2.0, scikit-learn | XGBoost 2.0.3, NumPy 1.26 | Supervised 70-feature behavioral anomaly classification model (`xgboost_behavioral_v1.bin`) producing candidate risk scores [0.00–1.00]. |
| **Computer Vision (CV)** | YOLOv8, SORT Tracker, EasyOCR | Ultralytics YOLOv8, PyTorch | Real-time vehicle license plate detection, Kalman-filter SORT multi-object tracking (`track_id`), and optical character recognition (ANPR). |
| **Multi-Modal Gemini NLP** | Google Gemini Flash 1.5, Groq LLaMA 3 | `google-generativeai` | Automated evidence document parsing, unstructured text entity extraction (people, vehicles, bank accounts), and structured triple mapping. |
| **Database ORM / Drivers** | SQLAlchemy 2.0, asyncpg, Neo4j Driver | SQLAlchemy 2.0 (AsyncIO) | Asynchronous connection pooling, PostgreSQL session lifecycle management, and Cypher driver execution. |

---

## 3. Workstation Pages & User Interface Deep Dive

CIVIX 2.0 features 13 specialized frontend workspace modules (`frontend/src/pages/`):

1. **`CaseWorkspacePage.tsx` (Case Management Engine)**:
   - Central hub for managing cases, assigning investigator permissions, configuring case ACLs (`READ`, `WRITE`, `ADMIN`), viewing entity dossiers, and tracking investigation milestones.
2. **`InvestigativeGraphPage.tsx` (Multi-Hop Graph Explorer)**:
   - Interactive multi-hop graph canvas (`GraphExplorer.tsx`, `GraphCanvas.tsx`) supporting 1H–5H expansions, node focus mode, path analysis panel (`PathAnalysisPanel.tsx`), investigator proposal creation (`ProposalDrawer.tsx`), relationship inspector (`RelationshipInspector.tsx`), and epistemic legend controls (`EpistemicLegend.tsx`).
3. **`EntityDossierPage.tsx` (Complete Entity Profiler)**:
   - Deep-dive dossier for any entity (`PERSON`, `VEHICLE`, `TELECOM`, `LOCATION`). Displays bitemporal attribute history, connected assertions, timeline of events, XGBoost risk scores, and linked evidence documents.
4. **`SpatialIntelligencePage.tsx` (GIS & Timeline Scrubber)**:
   - Interactive PostGIS spatial map rendering cell tower centroids, movement vectors, CCTV camera locations, and a time-range scrubber to analyze entity movement patterns over time.
5. **`TelecomIntelligencePage.tsx` (CDR & Cell Tower Analytics)**:
   - Call Detail Record (CDR) matrix aggregator (`TelecomMatrix.tsx`), co-location analysis across cell towers, subscriber call frequency heatmaps, IMEI/IMSI switching detectors, and night call volume charts.
6. **`CCTVCommandCenterPage.tsx` (Live Video & ANPR Tracker)**:
   - Multi-camera video feed monitoring dashboard (25 Delhi NCR streams), real-time ANPR license plate detection logs, SORT tracking ID persistence (`track_id`), and camera location map pins.
7. **`BiometricIntelligencePage.tsx` (Biometric Matching Interface)**:
   - Facial feature extraction, fingerprint pattern matching, biometric similarity scoring UI, and gallery comparison view.
8. **`EvidencePage.tsx` (Multi-Modal Evidence Vault)**:
   - Central document upload vault (`EvidenceVault.tsx`), PDF viewer, Gemini Flash 1.5 extracted entity tags, and court evidence chain-of-custody verification logs.
9. **`VisualAnalysisPage.tsx` (Visual Analytics Workspace)**:
   - Deep visual analytics workspace displaying bounding box overlays, object class distributions, and spatiotemporal visual clusters.
10. **`CommandCenterPage.tsx` (Executive Operational Dashboard)**:
    - High-level executive dashboard showing active case counts, pending supervisor assertion review counters, system telemetry indicators, and high-risk candidate alerts.
11. **`SearchPage.tsx` (Ask CIVIX Natural Language Search)**:
    - Natural language query bar powered by Gemini Flash 1.5, converting plain text questions (*"Show all calls between Suspect A and Suspect B in Jaipur during midnight"*) into SQL/Cypher queries.
12. **`FoundationTestPage.tsx` (System Diagnostic Console)**:
    - Internal engineering diagnostic panel verifying backend API availability, database connection health, and Neo4j connectivity.
13. **`CasesPage.tsx` (Case Directory)**:
    - Master list of all cases accessible to the logged-in investigator, filtered according to PostgreSQL Row-Level Security (RLS) policies.

---

## 4. Domain Ontology & Entity-Relation Model

CIVIX 2.0 uses a standardized, extensible domain ontology (`civix` PostgreSQL schema):

```
+-----------------------------------------------------------------------------------+
|                            CIVIX 2.0 DOMAIN ONTOLOGY                              |
+-----------------------------------------------------------------------------------+
| CORE ENTITIES (`civix.entity`):                                                    |
|   - PERSON           : Human target, suspect, victim, associate                   |
|   - VEHICLE          : Automobile, motorcycle, truck (Plate #, VIN, Make, Model) |
|   - TELECOM          : MSISDN (Phone #), IMSI, IMEI, Cell Tower Sector ID         |
|   - FINANCIAL        : Bank Account, UPI VPA, Credit Card, Wallet ID              |
|   - LOCATION         : GIS Point, Address, Landmark, Centroid (SRID 4326)         |
|   - ORGANIZATION     : Company, Shell Firm, Gang, Bank, Agency                    |
|   - EVIDENCE         : PDF Document, Image, Video Clip, Audio Recording           |
+-----------------------------------------------------------------------------------+
| SPATIOTEMPORAL EVENTS (`civix.event` & `civix.event_participant`):                 |
|   - CALL / MESSAGE   : Telecom communication event (Roles: CALLER, CALLEE, TOWER) |
|   - TRANSACTION      : Financial transfer event (Roles: SENDER, RECEIVER)         |
|   - CCTV_SIGHTING    : Video ANPR capture (Roles: SUBJECT, CAMERA_LOCATION)      |
|   - DEVICE_PING      : IPDR / Data session ping (Roles: DEVICE, CELL_TOWER)       |
+-----------------------------------------------------------------------------------+
| CONTROLLED PREDICATES (`civix.assertion` & `predicate_enum`):                     |
|   CALLED, MESSAGED, CO_LOCATED, REGISTERED_TO, OWNED_BY, DRIVER_OF, MEMBER_OF,   |
|   EMPLOYED_BY, ASSOCIATED_WITH, KNOWN_ASSOCIATE_OF, OBSERVED_AT, TRANSFERRED_TO,  |
|   RECEIVED_FROM, ALIAS_OF, LIVES_AT, WORKS_AT, FINANCES, HAS_SIM, USES_DEVICE,    |
|   TRANSACTED_WITH, PRESENT_AT                                                     |
+-----------------------------------------------------------------------------------+
```

---

## 5. Core Architectural Principles & Epistemic Separation

CIVIX 2.0 operates under strict engineering principles to eliminate AI hallucination, prevent unauthorized data leakage, and guarantee court-admissible evidence.

```
+-----------------------------------------------------------------------------------+
|                              EPISTEMIC SEPARATION MODEL                           |
+-----------------------------------------------------------------------------------+
| 1. OBSERVED FACTS         : Physical ground truth (CDRs, CCTV captures, Bank TXs) |
| 2. AI / ML INFERENCES    : System suggestions (XGBoost score, OCR, Gemini NLP)    |
| 3. HUMAN HYPOTHESES       : Investigator theories & stance support               |
| 4. INVESTIGATOR PROPOSAL  : PROPOSED relationship (Pending Supervisor Approval)   |
| 5. CONFIRMED FACT         : ACCEPTED_BY_SUPERVISOR -> Neo4j INVESTIGATOR_ASSERTED |
+-----------------------------------------------------------------------------------+
```

### The 5 Epistemic Invariants

1. **INV-01 (Fact Integrity)**: Observed ground truth (telecom logs, bank transfers, CCTV frames) is immutable and can never be mutated or overwritten by AI predictions or investigator assertions.
2. **INV-08 (No Autonomous AI/Investigator Confirmation)**: Neither AI inferences nor raw investigator proposals can self-confirm or directly alter the primary graph projection without supervisor approval.
3. **INV-18 (Controlled Predicates)**: All relationship types must conform to strict PostgreSQL `predicate_enum` definitions. Free-text strings are strictly prohibited.
4. **ADR-REM-02 (Unconfirmed Proposal Isolation)**: Relationships with status `PROPOSED` reside exclusively in PostgreSQL and are **NEVER** projected into the Neo4j graph traversal layer.
5. **ADR-REM-03 (Supervisor-Approved Projection)**: Only upon explicit supervisor review (`ACCEPTED_BY_SUPERVISOR`) does an outbox event trigger projection of an `INVESTIGATOR_ASSERTED` edge into Neo4j.

---

## 6. Major Limitations & Operational Gaps

1. **Government System Integrations**: CIVIX 2.0 does **NOT** connect to live government databases (CCTNS, NCRB, Aadhaar/UIDAI, telecom operator networks, or live police CCTV networks). All inputs use local uploads or synthetic test datasets.
2. **Neo4j Polling CDC Lag**: Graph projections rely on a periodic Python outbox worker (`worker/outbox_worker.py`). A 1–2 second synchronization delay exists between PostgreSQL commit and Neo4j edge availability.
3. **Biometric Face Search Backend**: The frontend biometric facial matching UI utilizes synthetic mock distance scores; live vector search (e.g. Pgvector/Milvus) is scheduled for Phase 2.

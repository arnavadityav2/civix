# CIVIX 2.0 — Presentation & Demo Playbook

**Document Status**: Authoritative Presentation & Defense Playbook  
**Audience**: Presenters, SIH Team Members, Technical Demonstrators  
**Authority Rule**: Derived directly from `docs/00_CIVIX_CURRENT_STATE.md` and repository code inspection.

---

## 1. Presentation Truth Table (Strict Honesty Rules)

| Category | Claim / Capability | Guidance & Required Wording |
| :--- | :--- | :--- |
| **YOU CAN SAY** | PostgreSQL System of Record | "CIVIX uses PostgreSQL 16 as its authoritative, bitemporal system of record with strict Row-Level Security." |
| **YOU CAN SAY** | Neo4j Graph Traversal | "Neo4j provides read-optimized 1-to-5 hop Cypher graph traversals synchronized via an Outbox CDC pattern." |
| **YOU CAN SAY** | Behavioral XGBoost Model | "CIVIX uses a deterministic 70-feature XGBoost model to score candidate risk scores based on CDR and financial metrics." |
| **YOU CAN SAY** | Multi-Modal Evidence OCR | "Unstructured evidence documents are parsed via Gemini Flash 1.5 into structured PostgreSQL entities and assertions." |
| **YOU CAN QUALIFY** | Computer Vision / CCTV | "The CV engine uses YOLOv8, SORT, and EasyOCR, currently running on a 25-camera Delhi NCR synthetic/demo video feed." |
| **YOU CAN QUALIFY** | Data Sources | "The platform is fully engineered for production data, currently demonstrated using synthetic CDR and financial datasets." |
| **YOU MUST NOT CLAIM** | Live Police Integrations | **NEVER CLAIM** live access to CCTNS, NCRB, Aadhaar/UIDAI, or live police CCTV feeds. State clearly: *"CIVIX is engineered to ingest these feeds via standard REST/gRPC interfaces, but is currently demonstrated using local benchmark datasets."* |
| **YOU MUST NOT CLAIM** | AI Absolute Truth | **NEVER CLAIM** AI makes final decisions. State: *"AI predictions are tagged as system inferences; only human supervisors can approve relationships into the graph."* |

---

## 2. Presentation Architecture Diagram

```
                +---------------------------------------+
                |           CIVIX INVESTIGATOR          |
                +---------------------------------------+
                                    |
                                    v
                +---------------------------------------+
                |        React 18 / Vite 5 Frontend     |
                |   (Cytoscape.js Graph, Leaflet Map)   |
                +---------------------------------------+
                                    |
                                    v
                +---------------------------------------+
                |       FastAPI Asynchronous Backend    |
                +---------------------------------------+
                                  /   \
                                 /     \
                                v       v
      +----------------------------+   +----------------------------+
      |      PostgreSQL 16 DB      |   |       Neo4j 5 Graph DB     |
      |   (Authoritative Store)    |   |    (Projection Traversal)  |
      |  - Row-Level Security      |   |  - 1 to 5 Hop Cypher      |
      |  - Bitemporal Schema       |   |  - Bounded 500 Node Cap    |
      |  - PostGIS Spatial Index   |   +----------------------------+
      +----------------------------+                 ^
                    |                                |
                    v                                |
      +-------------------------------------------------------------+
      |              Transactional Outbox CDC Worker                |
      |    - Polling `civix.outbox` -> Projections to Neo4j          |
      +-------------------------------------------------------------+
                                    |
                                    +---> ML & Computer Vision
                                          - XGBoost 70-Feature Engine
                                          - YOLOv8 + SORT + Plate OCR
                                          - Gemini Multi-Modal NLP
```

---

## 3. Step-by-Step SIH 10-Minute Live Demo Script

### Minute 0:00 – 1:30 | Problem Statement & Workstation Overview
- **Action**: Open `CommandCenterPage.tsx` showing high-level operational statistics.
- **Script**: *"Judges, law enforcement agencies face a major challenge: data arrives in isolated silos—telecom records, bank transfers, CCTV feeds, and PDF reports. CIVIX 2.0 unifies these sources into a single, security-enforced investigative workstation."*

### Minute 1:30 – 3:30 | Spatial Intelligence & Timeline Scrubber
- **Action**: Switch to `SpatialIntelligencePage.tsx`. Drag the spatiotemporal timeline scrubber. Click on a CCTV camera pin in Delhi NCR.
- **Script**: *"Here is our Spatial Subsystem. Built on PostGIS and Leaflet, it renders spatiotemporal centroids. As we scrub the timeline, we see movement patterns and live ANPR vehicle detections from our YOLOv8 and SORT tracker pipeline."*

### Minute 3:30 – 6:00 | Multi-Hop Graph Explorer & Epistemic Legend
- **Action**: Open `InvestigativeGraphPage.tsx`. Expand graph from 1-Hop to 3-Hop. Click on a node to view `EntityDossier.tsx`.
- **Script**: *"Notice the graph canvas powered by Cytoscape.js and Neo4j. In traditional SQL, 3-hop query joins take seconds. In CIVIX, Cypher returns paths instantly. Notice our Epistemic Legend: solid lines are physical telemetry facts, dashed lines are AI inferences, and yellow edges are supervisor-approved investigator assertions."*

### Minute 6:00 – 8:00 | Investigator Relationship Lifecycle & Proposal Drawer
- **Action**: Open `ProposalDrawer.tsx`. Select two entities, select predicate `KNOWN_ASSOCIATE_OF`, enter justification, and submit.
- **Script**: *"Can an investigator simply invent a relationship? No. When I submit this proposal, it is saved in PostgreSQL as `PROPOSED`. It is explicitly withheld from the Neo4j graph until a Supervisor approves it. Watch: as soon as the supervisor approves, our Outbox CDC worker projects the edge into Neo4j."*

### Minute 8:00 – 10:00 | Behavioral XGBoost Scoring & Evidence Vault
- **Action**: Open `TelecomIntelligencePage.tsx` and `EvidencePage.tsx`. Point to candidate risk scores.
- **Script**: *"Finally, our 70-Feature XGBoost model analyzes CDR and financial transaction metrics to generate candidate anomaly scores. Concurrently, Gemini Flash 1.5 extracts structured entities from uploaded PDF evidence. CIVIX provides complete, court-admissible evidence backing for every lead."*

---

## 4. "Judge Defense" Question & Answer Guide

### Q1: Why did you use BOTH PostgreSQL and Neo4j instead of just one?
> **Answer**: PostgreSQL is our single authoritative system of record because it provides ACID transactional guarantees, Row-Level Security (RLS), and PostGIS spatial indexing required for court admissibility. Neo4j is used as a read-optimized graph projection index to execute 1-to-5 hop Cypher traversals in milliseconds without locking the primary SQL database.

### Q2: How do you prevent cross-case data leakage between different police officers?
> **Answer**: At the database level, PostgreSQL Row-Level Security (RLS) policies filter every table using `current_setting('app.current_user_id')` joined against `civix.case_access`. At the graph level, every Cypher query explicitly injects `$authorized_case_ids` extracted from the user's validated JWT token.

### Q3: How do you ensure AI predictions don't pollute court evidence?
> **Answer**: CIVIX enforces strict epistemic separation. Ground truth facts (CDRs, CCTV logs) are immutable. AI models produce risk scores tagged as system inferences (`ASSERTED_BY = 'SYSTEM'`). They cannot alter PostgreSQL base tables or auto-confirm graph relationships without human supervisor authorization.

### Q4: Explain your XGBoost model. Is it generative AI?
> **Answer**: No, it is a deterministic 70-feature supervised machine learning model. It extracts 70 numerical features across 3 SQL CTE blocks (telecom metrics, financial transaction volumes, spatial spreads, demographic indicators) and outputs an anomaly score between 0.0 and 1.0.

### Q5: Can this system scale to national law enforcement volume (e.g. 1 million cases)?
> **Answer**: Yes. For graph queries, we enforce a strict 1-to-5 hop traversal depth and a hard limit of 500 nodes per request. For backend scaling, we recommend replacing our Python outbox polling worker with Apache Kafka and Debezium CDC for native Write-Ahead Log (WAL) streaming.

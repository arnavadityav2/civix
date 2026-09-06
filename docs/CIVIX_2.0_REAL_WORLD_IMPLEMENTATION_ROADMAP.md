# CIVIX 2.0 — Real-World Implementation & Deployment Blueprint

**Document Status**: Authoritative Production & Integration Blueprint  
**Audience**: System Architects, Government IT Directors, Security Auditors, Operations Engineers  
**Authority Rule**: Derived directly from `docs/00_CIVIX_CURRENT_STATE.md` and repository code inspection.

---

## 1. System Feature Maturity & Production Readiness Ledger

| Subsystem Module | Implementation Maturity | Backend Route / Service | Database & Tech Stack | Production Readiness Assessment |
| :--- | :--- | :--- | :--- | :--- |
| **Case ACL & Auth** | **PRODUCTION READY** | `/api/v1/cases`, `users.py` | PostgreSQL 16 RLS, JWT Auth | Fully hardened, unit-tested, court-admissible audit log |
| **Multi-Hop Graph** | **PRODUCTION READY** | `/api/v1/cases/{id}/graph` | Neo4j 5 Cypher, Cytoscape.js | Bounded 1–5 hop traversal, max 500 nodes UI cap |
| **Investigator Assertions** | **PRODUCTION READY** | `/api/v1/cases/{id}/assertions` | PostgreSQL `civix.assertion`, Outbox | Strict supervisor review workflow, outbox CDC |
| **Spatial Intelligence** | **PRODUCTION READY** | `/api/v1/spatial` | PostGIS GIS Centroids, Leaflet | Tested spatiotemporal map & timeline scrubber |
| **Telecom Intelligence** | **PRODUCTION READY** | `/api/v1/telecom` | PostgreSQL SQL CTE Aggregations | Full matrix analysis, co-location, CDR parsing |
| **Behavioral Scoring** | **PRODUCTION READY** | `/api/v1/cases/{id}/leads` | 70-Feature XGBoost Model | Deterministic SQL feature extractor & ML inference |
| **CCTV Command Center** | **STAGING READY** | `/api/v1/cctv` | YOLOv8, SORT, EasyOCR | Real CV engine running against 25 Delhi NCR streams |
| **Evidence Pipeline** | **STAGING READY** | `/api/v1/evidence` | Gemini Flash 1.5, PDF Parser | Multi-modal OCR & entity extraction pipeline |
| **Biometric Engine** | **PROTOTYPE / DEMO ONLY**| `/api/v1/biometric` | Synthetic Face/Fingerprint embeddings | Mocked similarity distance scoring UI |
| **Ask CIVIX NLP** | **PROTOTYPE / DEMO ONLY**| `/api/v1/search` | Gemini Flash 1.5, Full-Text SQL | Experimental natural language query parser |

---

## 2. Government System Integration Protocols & Adapter Specifications

While CIVIX 2.0 is demonstrated using synthetic datasets for hackathon evaluation, the backend architecture is explicitly decoupled from data providers. Connecting to live government systems requires deploying standardized gateway adapters:

```
+-----------------------------------------------------------------------------------+
|                        CIVIX 2.0 INGESTION ADAPTER GATEWAYS                       |
+-----------------------------------------------------------------------------------+
|  1. CCTNS Adapter         : REST/XML Wrapper -> Normalizes FIRs into `civix.person`  |
|  2. Telecom CDR Pipeline  : SFTP / S3 Poller -> Normalizes CDRs into `civix.event`   |
|  3. Banking FIU Adapter   : ISO 20022 / UPI Parser -> Bank transactions into `event`  |
|  4. CCTV RTSP Streamer    : ONVIF Discovery -> Feeds H.264/H.265 into YOLOv8 GPU     |
|  5. NATGRID Gateway       : OAuth2 mTLS -> Cross-agency entity resolution API     |
+-----------------------------------------------------------------------------------+
```

### A. CCTNS (Crime and Criminal Tracking Network & Systems) Adapter
- **Protocol**: HTTPS REST API / SOAP XML Web Services over Police VPN.
- **Payload Schema**: Ingests FIR (First Information Report) records, charge sheets, and arrest memos.
- **Normalization Mapping**: Maps suspect names, father names, and addresses into `civix.person` and `civix.entity` records with `entity_type = 'PERSON'`.

### B. Telecom Operator CDR/IPDR Ingestion Pipeline (Airtel, Jio, Vi)
- **Protocol**: Automated SFTP / AWS S3 encrypted bucket poller.
- **File Formats**: Standard CSV, TSV, or Apache Parquet CDR files.
- **Pipeline Processing**: Normalizes call timestamps, duration, A-Party (Caller), B-Party (Callee), Cell Tower ID, and First-Cell/Last-Cell coordinates into `civix.event` (`event_type = 'CALL'`) and `civix.event_participant`.

### C. Banking & Financial Intelligence Unit (FIU-IND) Adapter
- **Protocol**: Encrypted REST Gateway / ISO 20022 XML formats.
- **Payload Schema**: UPI transaction logs, NEFT/RTGS bank transfers, credit card ledger logs.
- **Normalization Mapping**: Maps transaction IDs, remitter accounts, beneficiary accounts, and amounts into `civix.event` (`event_type = 'TRANSACTION'`) and `civix.assertion` (`predicate = 'TRANSFERRED_TO'`).

### D. Smart City CCTV Camera Networks
- **Protocol**: RTSP (Real-Time Streaming Protocol) / ONVIF IP camera discovery.
- **Video Decoding**: Feeds raw H.264/H.265 video streams directly into Nvidia GPU worker nodes running YOLOv8 license plate detection and EasyOCR.

---

## 3. Production Infrastructure Architecture

```
                                POLICE INTRANET / SECURE GATEWAY
                                                |
                                                v
                                  +---------------------------+
                                  |    Nginx Reverse Proxy    |
                                  |  (SSL/TLS 1.3, Rate Limit)|
                                  +---------------------------+
                                                |
                                                v
                                  +---------------------------+
                                  |   Kubernetes Pod Cluster  |
                                  |   (FastAPI Uvicorn Nodes) |
                                  +---------------------------+
                                     /         |         \
                                    /          |          \
                                   v           v           v
                    +-------------------+ +----------+ +--------------------+
                    | PostgreSQL 16 HA  | | PgBouncer| | Neo4j 5 Enterprise |
                    | Primary / Replica | |  Pooler  | | Cluster (3 Core)   |
                    | + PostGIS GIS Ext | +----------+ | (Cypher Traversal) |
                    +-------------------+              +--------------------+
                              |                                  ^
                              | Write Outbox Event               | Read Projection
                              v                                  |
                    +-------------------------------------------------------+
                    |        Apache Kafka + Debezium CDC Pipeline           |
                    |     (Native PostgreSQL WAL Log Streaming Engine)      |
                    +-------------------------------------------------------+
                                              |
                                              v
                    +-------------------------------------------------------+
                    |             Nvidia GPU Worker Node Pool               |
                    |   (YOLOv8 Plate Detection + SORT + EasyOCR ANPR)      |
                    +-------------------------------------------------------+
```

---

## 4. Phase-by-Phase Real-World Rollout Strategy

### Phase 1: Local Police Station / Pilot District Deployment (Months 1–3)
- **Deployment Scope**: 5 trial police stations within a single metropolitan district.
- **Infrastructure**: Single-node Docker-Compose server (32-core CPU, 128GB RAM, 2TB NVMe SSD).
- **Data Operations**: Manual CDR CSV upload, PDF FIR file uploads, local case access control.
- **Target Outcome**: 100+ active cases managed with 0 cross-case data leakage.

### Phase 2: District HQ Consolidation & Range Expansion (Months 4–6)
- **Deployment Scope**: 50 police stations connected to District Headquarters.
- **Infrastructure**: High-Availability PostgreSQL Primary/Replica cluster with PgBouncer connection pooling.
- **Data Operations**: Automated SFTP CDR ingestion scripts, automated telecom matrix generation, supervisor proposal review workflow.
- **Target Outcome**: 5,000 active cases processed with sub-50ms graph Cypher query performance.

### Phase 3: State Data Center (SDC) Air-Gapped Deployment (Months 7–12)
- **Deployment Scope**: Statewide deployment (500+ Police Stations, 10,000 active investigators).
- **Infrastructure**: Air-Gapped Kubernetes (K8s) Cluster in State Data Center, Neo4j Enterprise Causal Cluster (3 Core + 2 Read Replicas), Nvidia A10G GPU inference cluster.
- **Security & Identity**: Integration with State Police Identity Provider (SAML 2.0 / OAuth2 SSO), Hardware Security Module (HSM) for JWT signing keys.
- **Air-Gapped AI**: Local LLM deployment (Ollama / LLaMA 3 70B / Local TrOCR) for zero-internet document processing.
- **Target Outcome**: 100,000+ cases, real-time CCTV ANPR feeds, state-level cross-case anomaly discovery.

### Phase 4: National Interoperability & Federation Framework (Months 13–18)
- **Deployment Scope**: Inter-state law enforcement federation.
- **Federated Architecture**: Cross-state federated query gateway allowing state agencies to query suspect links across state borders without exposing local case details.
- **Privacy Protections**: Anonymized entity hashing (SHA-256 hashed phone numbers/Aadhaar IDs) across state boundaries until formal inter-state clearance is granted.

---

## 5. Legal Compliance & Court Admissibility Framework

CIVIX 2.0 is specifically engineered to satisfy Indian legal evidence standards:

1. **Section 65B Indian Evidence Act Compliance**:
   - Every uploaded evidence file (CDRs, CCTV clips, PDFs) generates an automatic **Electronic Evidence Certificate**.
   - Cryptographic **SHA-256 hashes** are generated upon upload and stored immutably in PostgreSQL to guarantee evidence tampering detection.
   - All investigator views, downloads, and annotations are timestamped and logged in `civix.audit_log`.

2. **Epistemic Separation for Court Testimony**:
   - Defense lawyers cannot claim "AI hallucinated the evidence" because CIVIX explicitly separates physical ground truth (telecom CDRs) from AI risk scores (`ASSERTED_BY = 'SYSTEM'`).
   - Investigator proposals require explicit supervisor authorization (`ACCEPTED_BY_SUPERVISOR`) before altering the primary investigative graph.

---

## 6. Production Security & Hardening Checklist

- [ ] **PgBouncer Connection Pooler**: Deployed in transaction pooling mode to handle > 1,000 concurrent database connections.
- [ ] **Debezium CDC Streaming**: Replaces Python polling loop (`worker/outbox_worker.py`) with native WAL log streaming into Apache Kafka.
- [ ] **TLS 1.3 mTLS Encryption**: Enforce mutual TLS 1.3 encryption across all internal microservice calls and database connections.
- [ ] **Nvidia GPU Worker Nodes**: Provision Nvidia T4/A10G GPU nodes for real-time YOLOv8 video frame decoding and EasyOCR ANPR.
- [ ] **Hardware Security Module (HSM)**: Store JWT private signing keys in FIPS 140-2 Level 3 hardware security modules.
- [ ] **Automated Backup & Disaster Recovery**: Point-in-Time Recovery (PITR) for PostgreSQL WAL logs and automated Neo4j graph snapshots.

# CIVIX — COMPLETE CODEBASE FORENSIC REPORT

## Executive Summary
The CIVIX project is a sophisticated investigative case management platform currently in a state of partial implementation. It features extremely robust, "Bible-level" architectural documentation and a highly developed synthetic data generation pipeline (Golden World). The PostgreSQL database layer (schema, RLS, triggers) and the foundational FastAPI backend (authentication, JWT, case isolation) are successfully implemented and verified by tests. However, the system is fundamentally disconnected: there is no frontend, no Neo4j implementation, no real-data parsing pipelines, and the machine learning models (XGBoost) remain isolated in evaluation scripts rather than being integrated into the API. The project has drifted from its original Master Plan, executing Phase 8 API tasks under the umbrella of "Phase 7". 

## 1. Repository Structure
```text
/
├── civix_api/         # FastAPI backend implementation
├── civix_generator/   # Synthetic data generation engine
├── civix_ml/          # Machine learning features and models
├── data/              # Base data dependencies
├── database/          # PostgreSQL migrations and schema scripts
├── docs/              # Comprehensive project architecture documents
├── models/            # Saved ML artifacts (e.g., XGBoost models)
├── output/            # Generated synthetic data (CSV/JSON)
├── scratch/           # Experimental scripts and temporary logs
├── scripts/           # Utility and reporting scripts
├── tests/             # Pytest suites for the API
├── .env               # Environment configuration
├── pytest.ini         # Pytest configuration
└── requirements.txt   # Python dependencies
```
*Note: Directories such as `frontend`, `Docker`, `CI/CD`, and `graph/neo4j` are entirely absent from the repository.*

## 2. Complete File Inventory

| Path | Type | Purpose | Status | Dependencies | Important Notes |
| ---- | ---- | ------- | ------ | ------------ | --------------- |
| `civix_api/` | CORE | FastAPI backend application. | IMPLEMENTED | FastAPI, SQLAlchemy | Contains `auth`, `routers`, `dependencies.py`. |
| `database/migrations/` | CORE | PostgreSQL schema evolution. | IMPLEMENTED | Alembic (partially) | Contains 15 raw SQL migration scripts (`000` to `014`). |
| `civix_generator/` | CORE | Synthesizes 'Golden World' data. | WORKING | Pandas, Numpy | Highly developed; creates deterministic, billion-scale synthetic topologies. |
| `civix_ml/` | CORE | ML features, GNN research. | MIXED | PyTorch (frozen), XGBoost | GNN branch is frozen; XGBoost is available. |
| `models/` | GENERATED | Stored model binaries (`.pkl`). | GENERATED | joblib, scikit-learn | Contains trained XGBoost and Random Forest pipelines. |
| `output/` | DATA | CSV/JSON synthetic data outputs. | GENERATED | `civix_generator` | Used for ML training and database seeding. |
| `docs/` | DOCUMENTATION | Architecture and planning documents. | CORE | N/A | Contains 30+ detailed markdown files defining system behavior. |
| `tests/` | TEST | API integration testing. | PASSING | Pytest, HTTPX | 15/15 tests passing; strict RLS and JWT coverage. |
| `scratch/` | EXPERIMENTAL | Temporary evaluation scripts. | EXPERIMENTAL | Various | Contains test connections, smoke tests, and legacy graph prep scripts. |
| `scripts/` | SUPPORTING | General utilities. | MIXED | Python | Artifact scanners, schema inspectors. |
| `requirements.txt` | CONFIGURATION | Python package definitions. | CURRENT | Pip | Explicitly notes GNN dependencies are frozen due to Windows CPU constraints. |

## 3. Documentation Inventory

**Document:** `19_IMPLEMENTATION_MASTER_PLAN.md`
- **Purpose:** Defines the 14-phase implementation roadmap.
- **Authority level:** High (Original Master Plan)
- **Current/outdated:** Outdated (Actual implementation deviated in Phase 7).
- **Key decisions:** Requires strict gating before phases proceed.
- **Phases covered:** 0 through 14.
- **Conflicts:** Defines Phase 7 as "Neo4j Projection" and Phase 8 as "API/Backend", but current work executed API tasks under Phase 7.

**Document:** `CANONICAL_PHASE_7_HANDOVER.md`
- **Purpose:** Exhaustive state capture up to Phase 7 Task 2.
- **Authority level:** Highest (Immediate context source of truth).
- **Current/outdated:** Current up to the API test validation pause.
- **Phases covered:** Phase 1 to Phase 7 Task 2.
- **Tasks covered:** Phase 7 Task 1 (FastAPI/RLS), Phase 7 Task 2 (Implementation/Auth/Deadlock).
- **Dependencies:** Relies on Golden World synthesis.
- **Conflicts:** Ends abruptly without defining Phase 7 Task 3.

**Document:** `15_API_BACKEND_BIBLE.md`
- **Purpose:** Architectural requirements for the backend.
- **Authority level:** High.
- **Current/outdated:** Current.
- **Key decisions:** Enforces `civix.current_user_id` RLS session variables.
- **Tasks covered:** Defines 15 required MVP endpoints.

## 4. Roadmap / Phase Recovery
- **Phase 1-6:** Explicitly defined and marked complete (Architecture, Schema, Generation).
- **Phase 7:** Partially complete. 
  - **Task 1:** Complete (FastAPI & RLS Foundation).
  - **Task 2:** Complete (Case Creation, JWT Auth, Test Validation).
  - **Phase 7 Task 3: NOT DEFINED IN REPOSITORY**.
- **Phase 8-14:** Defined in `19_IMPLEMENTATION_MASTER_PLAN.md` (Authentication, ML Integration, Scale Expansion, Integration, Demo) but completely unstarted.
- **Conflicting Definitions:** The Master Plan defines Phase 7 as Neo4j Graph Projection and Phase 8 as API. However, the handover document executed API implementation under Phase 7. The Neo4j projection was skipped entirely.

## 5. Database Architecture
- **PostgreSQL version/configuration:** PostgreSQL 16/17 (Local/Native).
- **Schemas:** `civix` (primary operational data).
- **Tables:** Highly normalized schema adhering to bitemporal/provenance standards (`civix_user`, `investigative_case`, `case_access`, `person`, `event`, `audit_event`, etc.).
- **Relationships & Constraints:** Extensive usage of `DEFERRABLE INITIALLY DEFERRED` foreign keys to handle circular entity relationships.
- **Triggers:** Automated timestamps, audit triggers, and tombstone constraints.
- **Functions:** Custom RLS setup functions.
- **RLS policies:** Strict `FORCE ROW LEVEL SECURITY`. Uses `current_setting('civix.current_user_id', true)` for identity.
- **Roles:** `civix_api` (No superuser, No bypass RLS).
- **Privileges:** `civix_api` relies exclusively on application-level grants via case access roles.

## 6. Complete Database Entity Inventory
*(Subset of critical operational entities based on migration files)*

**Entity/Table:** `civix.investigative_case`
- **Purpose:** Core case container.
- **Primary Key:** `case_id` (UUID).
- **Columns/Types:** `case_number` (VARCHAR), `title` (VARCHAR), `status` (ENUM), `priority` (ENUM), `lead_investigator_id` (UUID).
- **Foreign Keys:** Links to `civix_user` (Lead Investigator).
- **RLS:** Active.
- **Status:** IMPLEMENTED and working in API.

**Entity/Table:** `civix.civix_user`
- **Purpose:** System users and investigators.
- **Primary Key:** `user_id` (UUID).
- **Unique:** `username`, `external_auth_id`.
- **Status:** IMPLEMENTED.

**Entity/Table:** `civix.case_access`
- **Purpose:** Maps users to cases with permission levels.
- **Foreign Keys:** `user_id` -> `civix_user`, `case_id` -> `investigative_case`.
- **RLS:** Used as the lookup matrix for broader RLS policies.
- **Status:** IMPLEMENTED.

**Entity/Table:** `civix.identity_resolution`
- **Purpose:** Tracks entity merges/deduplication.
- **Status:** IMPLEMENTED in schema, but UNUSED in code.

## 7. Migration Audit

| Migration | Purpose | Objects Added | Security Impact | Status |
| --------- | ------- | ------------- | --------------- | ------ |
| `000`-`001` | Extensions & Enums | `uuid-ossp`, `pgcrypto`, Core enums. | Foundation | COMPLETE |
| `002`-`004` | Users, Auth, Entities | `civix_user`, `person`, `organization`. | Identity baseline | COMPLETE |
| `007` | Cases & Access | `investigative_case`, `case_access`. | Establishes RBAC | COMPLETE |
| `013_rls.sql` | Row Level Security | RLS Policies on all operational tables. | High Security | COMPLETE |

**Final State:** A hardened PostgreSQL schema heavily reliant on database-level security and deferred constraints.

## 8. Backend/API Architecture
- **Application entrypoint:** `civix_api.main:app` (FastAPI).
- **Configuration:** `civix_api/config.py` (Pydantic BaseSettings, loads `.env`).
- **Authentication/JWT:** Custom middleware in `auth/principal.py` decoding `CIVIX_JWT_SECRET`.
- **DB session management:** SQLAlchemy AsyncSession (`database.py`), using context managers.
- **RLS session binding:** Custom dependency `get_rls_session` executes `SET LOCAL civix.current_user_id`.
- **Error handling:** Built-in FastAPI HTTPExceptions; handles SQLAlchemy `IntegrityError` explicitly to prevent pool death.

## 9. Endpoint Inventory

| HTTP Method | Path | Purpose | Authentication | RLS Dependency | Status |
| ----------- | ---- | ------- | -------------- | -------------- | ------ |
| `GET` | `/api/v1/users/me` | Fetch active profile | JWT Required | Yes | IMPLEMENTED |
| `POST` | `/api/v1/cases` | Create new case | JWT Required | Yes | IMPLEMENTED |
| `GET` | `/api/v1/cases` | List accessible cases | JWT Required | Yes | IMPLEMENTED |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve specific case | JWT Required | Yes | IMPLEMENTED |

*(All other endpoints defined in `15_API_BACKEND_BIBLE.md` such as `/cases/{id}/leads`, `/graph/neighbors`, `/ingest/cdr` are **MISSING**).*

## 10. Authentication & Authorization
- **JWT:** Implemented. Requires `sub` (user UUID) and `exp` claims. Validated via `HS256`.
- **Authorization:** `civix.case_access` table mapped against `civix.current_user_id` enforced directly by Postgres RLS, not application logic. 
- **Role:** Uses `civix_api` Postgres role.

## 11. Phase 7 Task 2 Verification
- **JWT:** ✅ Verified.
- **RLS / Cross-user isolation:** ✅ Verified (`test_case_list_and_get_isolated`).
- **Transaction-local identity:** ✅ Verified (`civix.current_user_id`).
- **Native civix_api role:** ✅ Verified (Confirmed via `test_runtime_negative_permissions`).
- **Pool/Rollback leakage:** ✅ Verified (Tests prove aborted transactions clear RLS context).
- **Deferred FK / IntegrityError:** ✅ Verified (Explicit error handlers implemented).
- **15/15 API tests:** ✅ Verified (COMPLETE).

## 12. Frontend Architecture
**MISSING.**
There are no frontend directories, UI frameworks (React/Vue), entry points, or components anywhere in the repository. The user interface does not exist.

## 13. ML Inventory
- **Model Name:** Canonical XGBoost & Random Forest.
- **Purpose:** Predicts `is_criminal` / anomaly likelihood.
- **Training dataset:** Golden World Synthetic Data (Profile A/B/C).
- **Saved artifact:** Stored in `models/phase3_backup/` as `.pkl` files (via `joblib`).
- **Inference code:** Present in `scratch/run_chunk3_inference.py`.
- **API integration:** **MISSING**. Models exist purely offline.
- **Current status:** TRAINED and EVALUATED. Inference is available locally but completely disconnected from the API.

## 14. XGBoost Status
- **Trained:** Yes.
- **Evaluated:** Yes.
- **Inference Available:** Yes (via scratch scripts).
- **API Integrated:** NO.
- **Real-Data Validated:** NO (Only validated on synthetic data).

## 15. GraphNest / GNN Status
- **Status:** **FROZEN / ABANDONED (EXPERIMENTAL)**.
- **Reason:** Attempted PyTorch Geometric (PyG) and GraphSAGE training on the synthetic network. Failed due to missing C++ compilation backends (`pyg-lib`, `torch-sparse`) in the local Windows CPU environment.
- **Decision:** The GNN research branch was explicitly frozen. The canonical edge graphs are preserved, but the model is not part of the production API path.

## 16. Neo4j / Graph Status
- **Status:** **DOCUMENTED ONLY / MISSING**.
- **Evidence:** `19_IMPLEMENTATION_MASTER_PLAN.md` dictates Neo4j projection as Phase 7, and `generate_reports.py` contains Neo4j tombstone audit definitions.
- **Implementation:** There is zero Neo4j connection code, zero Cypher logic, zero CDC (Change Data Capture) outbox logic, and no `neo4j` dependencies in `requirements.txt`.

## 17. Synthetic Data Pipeline
- **Status:** **VERIFIED WORKING**.
- **Mechanics:** Located in `civix_generator/`. Deterministically creates billions of edges (telecom, financial, spatial) driven by random seeds. Outputs to `output/` and `output_run1/` via Pandas/PyArrow.
- **Ingestion:** Handled via `database/ingest_golden_world.py` which pushes the synthetic CSVs directly into the PostgreSQL schema.

## 18. Real-Data Readiness
| Data Source | Supported? | Parser | DB Ingestion | ML Ready |
| ----------- | ---------- | ------ | ------------ | -------- |
| FIRs | NO | Missing | Missing | Missing |
| CDRs | NO | Missing | Synthetic Only | Missing |
| Financials | NO | Missing | Synthetic Only | Missing |
| Surveillance | NO | Missing | Synthetic Only | Missing |

*The system is strictly locked into the synthetic "Golden World". It currently has **zero capability** to parse, normalize, or ingest real-world formats (CSV/JSON/XML) from external agencies.*

## 19. Entity Resolution
- **Status:** **DOCUMENTED ONLY**.
- **Evidence:** Database tables (`identity_resolution`, `identity_merge_event`) exist in the migrations.
- **Implementation:** There is absolutely no entity resolution logic (deterministic, fuzzy, or ML-based) in the Python codebase.

## 20. NLP
- **Status:** **MISSING**.
- **Evidence:** A global repository search for `nlp`, `ner`, `spacy`, and `transformers` yielded zero implementation files. No NLP capabilities currently exist.

## 21. Data Pipeline
```text
INPUT                 [MISSING]
 ↓
RAW DATA              [MISSING]
 ↓
PARSING               [MISSING]
 ↓
NORMALIZATION         [MISSING]
 ↓
IDENTITY RESOLUTION   [MISSING]
 ↓
CANONICAL DATABASE    [IMPLEMENTED] (Via synthetic direct-ingest)
 ↓
FEATURE ENGINEERING   [PARTIAL] (Offline only)
 ↓
ML                    [PARTIAL] (Offline only)
 ↓
GRAPH (Neo4j)         [MISSING]
 ↓
API                   [PARTIAL] (Foundation only)
 ↓
FRONTEND              [MISSING]
```

## 22. Testing
- **API Tests (`tests/api/`):** 15/15 tests covering JWT authentication, RLS leakage, and database rollback isolation. Status: PASSING.
- **Database Tests:** Embedded in Python scratch validation scripts (`verify_phase2a.py`, `verify_large_dataset.py`).
- **Frontend/ML Tests:** None.

## 23. Configuration & Environment
- **Configuration:** Managed via `.env` (exists) and `civix_api/config.py`.
- **Dependencies:** Purely native installations. No Docker or `docker-compose.yml` configurations exist for the API or Database. 
- **Flags:** `CIVIX_JWT_SECRET` is heavily required for the API to boot.

## 24. Dependencies
- **Required:** `FastAPI`, `SQLAlchemy`, `psycopg[binary]`, `alembic`, `pydantic`, `PyJWT`.
- **Data/ML:** `duckdb`, `xgboost`, `pandas`, `scikit-learn`, `pyarrow`.
- **Frozen/Experimental:** `torch`, `torch_geometric` (commented out in `requirements.txt`).
- **Missing:** `neo4j`, `celery`/`kafka` (for CDC).

## 25. Git / Change History
- **Status:** The repository is heavily untracked.
- **Uncommitted Changes:** 47+ files are completely untracked (including `civix_api/`, `tests/`, and massive `scratch/` artifacts). 
- **Last Commit:** `Phase 5 Complete - Initial Commit` (Shows that everything from Phase 6 and 7 has never been committed to source control).

## 26. Documentation vs Code Discrepancies
| Area | Documentation Says | Code Does | Actual Status | Discrepancy |
| ---- | ------------------ | --------- | ------------- | ----------- |
| Roadmap | Phase 7 is Neo4j | Phase 7 built the API | Out of sync | Major planning collision. |
| Graph | Neo4j scales the UI | No Neo4j code exists | Missing | Graph is a core promised feature. |
| Features | API surfaces leads/ML | API only does case CRUD | Partial | Disconnected from ML entirely. |
| Ingestion | System parses real data | Code only ingests synthetic | Missing | Blocked from real-world usage. |

## 27. Dead / Experimental Components
- **`scratch/` directory:** Contains ~50 files (`install_native_postgres_v*.ps1`, `run_chunk*.py`, `test_cte.sql`). These are heavily experimental and should be categorized as **KEEP (Ignore)** until officially deprecated.
- **GNN Code:** `gnn_exp3_prep.py` is dead code due to environment freezing.

## 28. Current Architecture Map
```text
      [ EXTERNAL WORLD - DISCONNECTED ]
                   ✖ (No Parsers)
                   
          ┌───────────────────────┐
          │   civix_generator     │ (Synthetic)
          └──────────┬────────────┘
                     │
          ┌──────────▼────────────┐
          │   PostgreSQL (civix)  │ ◄──┐ (Direct DB Auth)
          └──────────┬────────────┘    │
                     │                 │
          ┌──────────▼────────────┐    │
          │      civix_api        │ ───┘
          │ (Cases, Users, Auth)  │
          └──────────┬────────────┘
                     │
                     ✖ (No Frontend UI exists)
                     
          ┌───────────────────────┐
          │   XGBoost / ML        │ (Offline Only - No API link)
          └───────────────────────┘
```

## 29. What Works Today
## 🟢 VERIFIED WORKING
- **PostgreSQL Schema:** Fully hardened, RLS enforced, triggers active.
- **Synthetic Generator:** Can synthesize millions of realistic records.
- **FastAPI Core:** Securely authenticates JWTs and isolates RLS queries per user.
- **Offline ML:** XGBoost can train on the synthetic data and achieve strong ROC-AUC.

## 30. What Is Incomplete
## 🔴 MISSING
- Phase 7 Task 3 Definition
- Frontend / Web Interface
- Neo4j Graph Database Integration
- Real-world data ingestion pipelines (FIR, CDR parsing)
- Entity Resolution Engine
- NLP / LLM extraction capabilities
- API integration for ML/Leads

## 31. Real Prototype Gap Analysis
To achieve **a functioning CIVIX prototype operating on authorized real investigative data**, the following gaps must be closed:

### MUST HAVE (Blocking real-data prototype)
1. **Real-Data Ingestion API:** Endpoints and parsers to accept raw CDRs and FIR CSVs.
2. **ML API Integration:** A service layer connecting the FastAPI backend to the trained XGBoost inference pipeline.
3. **Frontend UI:** A minimal investigator dashboard to visualize cases, upload data, and view ML-generated leads.

### SHOULD HAVE
1. **Entity Resolution:** Basic deterministic deduplication for incoming data.

### FUTURE / PRODUCTION
1. **Neo4j Graph Database:** Can be deferred; the current prototype can operate directly on PostgreSQL via SQL joins for basic network visualization.
2. **GNNs / PyTorch:** Completely unnecessary for initial MVP.

## 32. Phase Status
- **Phase 7 Task 1:** 🟢 COMPLETE
- **Phase 7 Task 2:** 🟢 COMPLETE (15/15 tests passing, RLS/JWT verified).
- **Phase 7 Task 3:** ⚠️ **NOT DEFINED IN CURRENT REPOSITORY**

## 33. Critical Findings
1. **Context Drift in Master Plan:** The system executes Phase 8 API logic under the guise of "Phase 7".
2. **Git Neglect:** Over 40 critical files (the entire backend and test suite) have never been committed to Git.
3. **ML Disconnect:** The data science environment (`civix_ml`, XGBoost) is entirely disconnected from the software engineering environment (`civix_api`). There is no bridge to serve ML predictions to users.

## 34. Recommended Next Step
**Realign the Project Roadmap:**
Since Phase 7 Task 3 does not exist, and the API foundation is established, the next logical step is to write an architectural bridge defining how ML inference (XGBoost leads) and data ingestion will be exposed through the `civix_api`, and to begin building the initial Frontend UI.

---

# CIVIX CURRENT STATE — ONE-PAGE SUMMARY
```text
CURRENT PHASE: Phase 7 / 8 (API Backend Implementation)
CURRENT TASK: Blocked (Task 3 definition missing)
TASK 2 STATUS: COMPLETE (15/15 tests passing)
BACKEND STATUS: FOUNDATION IMPLEMENTED (Auth, JWT, Case CRUD)
DATABASE STATUS: FULLY HARDENED (RLS, Deferred FKs active)
FRONTEND STATUS: MISSING (0% implemented)
XGBOOST STATUS: TRAINED & EVALUATED (Offline only, no API integration)
GRAPHNEST STATUS: ABANDONED (Frozen due to environment constraints)
NEO4J STATUS: MISSING (Documented, but zero implementation)
SYNTHETIC DATA STATUS: WORKING (Billion-scale deterministic generation)
REAL DATA STATUS: MISSING (Zero parsing/ingestion capability)
NLP STATUS: MISSING
ENTITY RESOLUTION STATUS: MISSING (Schema exists, logic absent)
TEST STATUS: PASSING (Core API tests green)
BIGGEST CURRENT BLOCKER: Missing definition for Task 3 and no Git commits for recent work.
NEXT LOGICAL WORK: Integrate XGBoost inference into FastAPI / Build Real-Data Ingestion endpoints.
DISTANCE TO REAL PROTOTYPE: MEDIUM-FAR (Requires Frontend, Real-Data Parsers, and ML-API bridge).
```

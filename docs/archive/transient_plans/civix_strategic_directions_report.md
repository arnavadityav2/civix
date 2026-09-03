# CIVIX — STRATEGIC DIRECTIONS REPORT

## Executive Summary
Following the codebase forensic audit, it is clear that CIVIX possesses a highly advanced backend foundation—featuring a fully hardened PostgreSQL database with RLS, a functioning FastAPI core, and a powerful synthetic data generator. However, the system is fundamentally siloed. The machine learning models operate completely offline, and there is zero user interface or real-world data ingestion capability. 

Because the project halted without defining **Phase 7 Task 3**, we are at a strategic pivot point. This report outlines the exact, detailed directions the project should proceed in to evolve from a disconnected set of backend services into a functioning investigative prototype.

---

## Strategic Direction 1: The ML-API Bridge (The Missing Link)

Currently, the XGBoost models are trained and have high predictive accuracy on the synthetic "Golden World" dataset, but they live entirely inside isolated Python scratch scripts (`civix_ml`). The FastAPI application (`civix_api`) is completely unaware of these models. 

**Where we should proceed:**
We must build the bridge between the API and the ML models. This should be officially designated as **Phase 7 Task 3**.

**Detailed Actions:**
1. **Model Hosting:** Integrate `joblib` into the FastAPI startup lifecycle to load the pre-trained XGBoost `.pkl` artifact securely into memory.
2. **Feature Pipeline Integration:** Port the inference logic from `run_chunk3_inference.py` directly into a FastAPI service class. When the API queries an entity, it must dynamically extract the 59 features required by the model.
3. **The Leads Endpoint:** Create the `GET /api/v1/cases/{case_id}/leads` endpoint. This endpoint will execute the model inference in real-time (or query pre-computed offline scores) and return ranked anomalies (e.g., suspicious financial bursts or telecom patterns) to the investigator.
4. **Explainability:** Ensure the API doesn't just return a "fraud score", but explicitly returns the top contributing features (e.g., "High Call Frequency at 2AM") so investigators can understand *why* the AI flagged the entity.

---

## Strategic Direction 2: Real-World Data Ingestion (Breaking the Synthetic Constraint)

The system currently relies 100% on `civix_generator`, which deterministically synthesizes billions of edges directly into the database. While incredible for scale testing, the system currently has absolutely zero capability to ingest real-world formats.

**Where we should proceed:**
We must build the **Ingestion & Parsing Pipeline**. This should be designated as **Phase 8**.

**Detailed Actions:**
1. **Format Parsers:** Build Python parsers capable of reading standard investigative artifacts. The highest priorities should be:
   * **Telecom CDRs:** Parsing CSVs containing `caller`, `receiver`, `timestamp`, `duration`, and `cell_tower`.
   * **Financial Ledgers:** Parsing standard banking transaction CSVs.
   * **FIRs (First Information Reports):** Basic structured metadata parsing for case initialization.
2. **Ontology Mapping:** The parsers must cleanly map raw CSV data into the strict `civix` ontology (e.g., translating a raw phone number string into a canonical `civix.telecom_number` entity, and a call into a `civix.event`).
3. **Deterministic Entity Resolution:** Implement basic deduplication logic. If a CDR contains a phone number that already exists in the database, the ingestion pipeline must link the new event to the existing entity rather than creating a duplicate.

---

## Strategic Direction 3: The Investigator Frontend UI

The entire API is currently headless. Investigators cannot see cases, run searches, or view graph relationships.

**Where we should proceed:**
We must stand up the **Investigator Dashboard**. This should be designated as **Phase 9**.

**Detailed Actions:**
1. **Framework:** Initialize a modern React (or Next.js) web application.
2. **Auth & State:** Implement JWT negotiation and secure storage to authenticate with the existing FastAPI backend.
3. **Case Management View:** A UI workspace to view the details of an `investigative_case`, including attached suspects, organizations, and evidence.
4. **Relational Graph Explorer:** Since Neo4j is not implemented, the frontend should use a lightweight visualization library (like `react-flow` or `cytoscape.js`) to render the PostgreSQL foreign-key entity relationships as a visual network graph for the investigator.
5. **AI Triage Inbox:** A dedicated UI panel where investigators can view the AI-generated leads (from Strategic Direction 1) and click "Accept" or "Reject".

---

## What We Should DEFER (Do Not Proceed With Yet)

Based on the audit, certain planned features should remain frozen to avoid unnecessary complexity during prototype development:

1. **Neo4j Graph Projection:** Defer. The PostgreSQL relational schema is robust enough to serve basic graph topologies to a frontend via recursive CTEs or standard joins. Synchronizing an external Neo4j database via CDC (Change Data Capture) is too heavy for the immediate prototype.
2. **Graph Neural Networks (GNN):** Defer. The GNN branch failed due to missing Windows C++ dependencies. The XGBoost model is already working and is far easier to integrate into the API.
3. **LLM / Deep NLP Extraction:** Defer. Focus on structured data ingestion (CDRs/Financials) before attempting unstructured text extraction from raw documents.

---

## Final Recommendation on Immediate Next Step

The most logical, highest-value immediate action is to tackle **Strategic Direction 1**. 

We should formally define **Phase 7 Task 3** as: 
> **"Integrate the offline XGBoost inference pipeline into the FastAPI backend and expose the AI leads via a secure, RLS-protected endpoint."**

This instantly unlocks the value of your ML work and bridges the software engineering side with the data science side.

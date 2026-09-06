# CIVIX 2.0 — DEMO SCREEN MAP: DWARKA SECTOR 23 CASH VAN ROBBERY

> **PURPOSE**: A step-by-step UI navigation guide for the presenter to ensure a smooth, error-free demonstration.
> **RULE**: Do not deviate from these routes during the live demo to avoid hitting un-seeded mock data.

---

### STEP 1: Global Dashboard
* **Route**: `/` (or `/dashboard`)
* **Action**: 
  1. Highlight the global metrics (Total Cases, Active Entities).
  2. Explain the difference between PostgreSQL (System of Record) and Neo4j (Graph Intelligence).
  3. In the "Recent Cases" or "Search" bar, click on **CIV-2012-001**.
* **Transition**: "Let's dive into a 14-year-old cold case..."

---

### STEP 2: Case Overview (CIV-2012-001)
* **Route**: `/cases/CIV-2012-001`
* **Action**:
  1. Point out the basic metadata: Date Opened (2012-03-14), Status (CLOSED_SOLVED).
  2. Briefly scroll through the **Entities** list, highlighting convicted robbers (Rakesh Yadav, Devender Nagar).
  3. Mention the missing mastermind: Suresh Valmiki, and the unknown recruiter.
* **Transition**: "To understand the unknown recruiter, we need to look at the historical evidence ingested by our NLP engine."

---

### STEP 3: Evidence Tab
* **Route**: `/cases/CIV-2012-001/evidence`
* **Action**:
  1. Scroll down to **EVD-001-008** (Interrogation Transcript).
  2. Point to **EVD-001-012** (Police Sketch - Person Unknown 05).
  3. Explain that NLP automatically extracted the entity 'Person Unknown 05' from the legacy unstructured PDFs.
* **Transition**: "For 14 years, this sketch was all we had. Let's see what CIVIX 2.0 Graph Intelligence makes of it today."

---

### STEP 4: Graph Intelligence Canvas
* **Route**: `/graph?case=CIV-2012-001` (or via the Graph tab in the case view)
* **Action**:
  1. Ensure the central node is `CIV-2012-001`.
  2. Double-click the node for **Person Unknown 05** to expand their network.
  3. Open the **AI Leads** side-panel.
  4. Highlight lead **EVD-001-020**: The system asserts that 'Person Unknown 05' is actually **Vikram Sharma** (arrested in 2026 for case CIV-2026-009).
* **Transition**: "The AI is confident, but an investigator needs hard spatial evidence to corroborate this link."

---

### STEP 5: Telecom & Spatial Intelligence Map
* **Route**: `/telecom-intelligence` (or `/spatial`)
* **Action**:
  1. Ensure the active case in context is `CIV-2012-001`.
  2. Point out the cell tower radius for **TOWER-DW-01** at 07:38 AM (CDR Evidence EVD-001-004).
  3. Toggle the **ANPR Layer** to show the NH-48 Toll capture at 06:52 AM.
  4. Explain how the XGBoost anomaly model flags this movement pattern, linking Vikram Sharma's newly discovered historical SIM card to this exact route.
* **Transition**: "With the graph resolution backed up by spatial telemetry, we have our proof."

---

### STEP 6: Assertions & Final Verification
* **Route**: `/cases/CIV-2012-001/assertions` (or Assertions Inbox `/assertions`)
* **Action**:
  1. Locate the pending AI assertion linking Vikram Sharma to CIV-2012-001.
  2. Review the epistemic confidence score.
  3. Click **ACCEPT** / **AUTHORIZE**.
* **Final Script Point**: "By confirming this assertion, Vikram Sharma is permanently encoded into the master graph as the recruiter for the 2012 robbery. The CDC Outbox instantly syncs this truth across all connected government databases. A 14-year-old cold case, solved."

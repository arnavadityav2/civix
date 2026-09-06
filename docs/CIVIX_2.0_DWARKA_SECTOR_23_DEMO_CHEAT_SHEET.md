# CIVIX 2.0 — DEMO CHEAT SHEET: DWARKA SECTOR 23 CASH VAN ROBBERY

> **FOR INTERNAL USE ONLY**
> Keep this document open during the live SIH demonstration to ensure all entity IDs, case numbers, and search terms perfectly match the synthetic dataset.

## 1. Case Details
* **Case Number**: `CIV-2012-001`
* **Title**: Dwarka Sector 23 Cash Van Robbery
* **Incident Type**: Criminal (Armed Robbery)
* **Date Opened**: 2012-03-14
* **Status**: CLOSED_SOLVED
* **Jurisdiction**: Dwarka PS, Delhi

## 2. Key Entities (Persons)

| Name | Role / Basis | Status / Notes | ID Reference |
| :--- | :--- | :--- | :--- |
| **Suresh Valmiki** | SUSPECT (Gang Leader) | Mastermind. Arrested in 2026 (Najafgarh). | `637038f4-633f-8457-6de9-b7142bc10381` |
| **Vikram Sharma** | SUSPECT (Recruiter) | The Missing Link (Alias: "Pandit" / Person Unknown 05). Identified in 2026. | `7bfb4b76-8bee-ccaf-10a6-009a09e6fc04` |
| **Rakesh Yadav** | ACCUSED (Robber) | Convicted RI 7 Years. Mentions "Pandit". | `9df4b44a-e753-0b93-20f7-1f5b3868a229` |
| **Mohinder Bhati** | ACCUSED (Robber) | Convicted. Alias: "Bhura". | `b217c43c-4932-0d58-5df4-821dfec60816` |
| **Ramesh Chauhan** | ACCUSED (Inside caller) | Convicted. | `cfddd55c-7d3d-9950-1782-2b05dd13dc58` |
| **Devender Nagar** | ACCUSED (Driver) | Convicted Getaway Driver. | `be6525aa-5d23-6398-2eb5-aee1aa309b7a` |
| **Anita Mehta** | VICTIM (Guard) | SBI Guard. Injured in shootout. | `263f32c4-30fd-40a8-b01b-6def1b47e90c` |
| **Ram Karan Singh** | VICTIM (Driver) | SBI Cash Van Driver. | `09d7a50a-82dd-4acf-1c8c-ed1d70f5b332` |

## 3. Key Entities (Vehicles)
* **Registration**: `HR-25-BC-9921`
* **Make/Model**: Hero Splendor (Motorcycle)
* **Color**: Black
* **Role**: SUBJECT_VEHICLE (Getaway vehicle captured on ANPR)

## 4. Crucial Evidence Artifacts to Highlight
_Use these exact terms/IDs when searching or filtering in the UI._

1. **EVD-001-008 (Interrogation Transcript)**: 
   * Mentions the alias 'Pandit'.
   * *Talking Point*: NLP Entity Extraction pulling names from unstructured PDFs.
2. **EVD-001-012 (Police Sketch)** & **EVD-001-013 (Lookout Circular)**: 
   * Initial dead-end leads for Person Unknown 05.
3. **EVD-001-020 (AI Lead)**: 
   * The critical intelligence hit linking Person Unknown 05 to Vikram Sharma (P0075).
   * *Talking Point*: Neo4j Graph Resolution across 14 years.
4. **EVD-001-004 (CDR)**: 
   * Call Data Record hitting TOWER-DW-01 at 07:38 AM.
5. **EVD-001-011 (ANPR Data)**: 
   * NH-48 Toll capture of the motorcycle convoy at 06:52 AM.

## 5. Connections to Other Cases
If the judges ask about cross-case intelligence, mention that Vikram Sharma and Suresh Valmiki were finally caught because of their involvement in **CIV-2026-009 (Najafgarh Robbery & Suresh Valmiki Arrest)**.

## 6. Technical Capabilities Demonstrated
When clicking through the UI, ensure you verbally state which backend technology is powering the screen:
* **Evidence Uploads / NLP**: Gemini API (Entity Extraction)
* **Graph Canvas**: Neo4j (Identity Resolution, Multi-hop tracking)
* **Spatial/Telecom Map**: PostgreSQL + PostGIS + XGBoost (Behavioral Anomaly)
* **Assertions Panel**: CDC Outbox Pattern (Syncing Postgres to Neo4j)

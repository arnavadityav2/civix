# CIVIX 2.0 — DEMO STORY: DWARKA SECTOR 23 CASH VAN ROBBERY

> **CLASSIFICATION**: RESTRICTED / SYNTHETIC DEMONSTRATION DATASET
> **TARGET AUDIENCE**: SIH Judges, Technical Evaluators
> **DEMO DURATION**: 8-12 Minutes

## 1. Introduction and Setup (1 Minute)
**Objective**: Hook the audience by introducing a "cold case" with a missing puzzle piece, and explaining how CIVIX 2.0 is designed to bridge historical data with active intelligence.

* **Speaker Script**: "Welcome to the CIVIX 2.0 Demonstration. Today, we are putting ourselves in the shoes of a Delhi Police Crime Branch Investigator. We are going to look at a case from 2012: the Dwarka Sector 23 Cash Van Robbery. Back then, ₹47 Lakhs was looted. Four men were caught and convicted, but the mastermind, a gang leader named Suresh Valmiki, and an unknown recruiter known only as 'Person Unknown 05' or 'Pandit' escaped. For 14 years, the trail was cold. Today, we're going to use CIVIX 2.0 to finally close it."

## 2. The Case Dashboard & Legacy Evidence (2 Minutes)
**Objective**: Show that CIVIX can digitize and structure unstructured historical evidence.

* **Action**: Investigator opens **Case CIV-2012-001** on the Dashboard.
* **Speaker Script**: "When we open the case file, we don't just see a PDF of FIR 127/2012. CIVIX has ingested the original files, including the SBI guard's injury report, the seizure memo for the getaway motorcycle (HR-25-BC-9921), and the original 2013 interrogation transcript of convicted robber Rakesh Yadav."
* **Action**: Investigator navigates to the **Evidence Tab**.
* **Highlight**: Point out **EVD-001-008 (Interrogation Transcript)** and **EVD-001-012 (Police Sketch)**. 
* **Speaker Script**: "In his 2013 interrogation, Rakesh Yadav mentioned a recruiter called 'Pandit'. A police sketch was made (Person Unknown 05), and a Lookout Circular was issued, but he was never identified. Notice how CIVIX's NLP engine has automatically extracted 'Person Unknown 05' as an entity from these PDFs."

## 3. The Graph Resolution (3 Minutes)
**Objective**: Demonstrate the Neo4j Knowledge Graph and Identity Resolution.

* **Action**: Investigator opens the **Graph Intelligence Canvas** for CIV-2012-001.
* **Speaker Script**: "This is where the magic happens. We ask CIVIX to expand the network around 'Person Unknown 05'. CIVIX cross-references millions of data points—telecom records, recent FIRs, and financial overlaps."
* **Action**: The investigator clicks "Expand Network" or views the AI Leads.
* **Highlight**: Show AI Lead **EVD-001-020: Person Unknown 05 = Vikram Sharma**.
* **Speaker Script**: "Here, our AI resolution engine flags a high-confidence match. A recent arrest in a 2026 Najafgarh Robbery (CIV-2026-009) brought in a man named Vikram Sharma. Our ML pipeline matches the historical police sketch, the alias 'Pandit' from modern telecom chatter, and spatial overlaps to conclude that Vikram Sharma IS 'Person Unknown 05'."

## 4. Telecom & Spatial Corroboration (3 Minutes)
**Objective**: Prove the AI assertion using hard data (XGBoost, PostGIS).

* **Action**: Investigator switches to the **Telecom & Spatial Intelligence Module**.
* **Speaker Script**: "An AI assertion isn't enough for a conviction; we need evidence. Let's look at the spatial data. CIVIX pulled an old CDR from a Dwarka cell tower (EVD-001-004) recorded at 07:38 AM on the day of the 2012 robbery."
* **Action**: Investigator layers ANPR data (EVD-001-011).
* **Speaker Script**: "Now we layer ANPR data from the NH-48 Toll plaza. We see the black Hero Splendor motorcycle (HR-25-BC-9921) moving in convoy at 06:52 AM. The phone number pinging the Dwarka tower was traced to a SIM recently linked to Vikram Sharma's modern device network."

## 5. The Assertion and Conclusion (1-2 Minutes)
**Objective**: Show the investigator's final action to permanently link the suspect.

* **Action**: Investigator navigates to the **Assertions Panel**.
* **Speaker Script**: "Based on the Graph Resolution, the historical CDR, and the ANPR toll overlap, we have our proof. As the lead investigator, I will now formally accept the AI lead."
* **Action**: Investigator clicks `ACCEPT` on the assertion linking Vikram Sharma to CIV-2012-001.
* **Speaker Script**: "By approving this assertion, Vikram Sharma is permanently linked to the 2012 Cash Van Robbery across the entire state database. The gang leader, Suresh Valmiki, was also caught in the 2026 raid. A 14-year-old cold case is solved in minutes using data integration and spatial AI. That is the power of CIVIX 2.0."

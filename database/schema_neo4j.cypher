// ==============================================================================
// CIVIX Platform — Neo4j Cypher Schema (Intelligence Engine)
// Derived from implementation_plan.md
// Phase 7 Step 4: Corrected Identifiers and last_seq_no Support
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. UNIQUENESS CONSTRAINTS (Ensures no duplicate entities are created)
// ------------------------------------------------------------------------------

CREATE CONSTRAINT unique_person IF NOT EXISTS FOR (p:Person) REQUIRE p.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_identity IF NOT EXISTS FOR (i:Identity) REQUIRE i.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_phonenumber IF NOT EXISTS FOR (ph:PhoneNumber) REQUIRE ph.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_device IF NOT EXISTS FOR (d:Device) REQUIRE d.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_vehicle IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_financial_account IF NOT EXISTS FOR (a:FinancialAccount) REQUIRE a.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_property IF NOT EXISTS FOR (pr:Property) REQUIRE pr.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_location IF NOT EXISTS FOR (l:Location) REQUIRE l.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_organization IF NOT EXISTS FOR (o:Organization) REQUIRE o.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_network IF NOT EXISTS FOR (n:Network) REQUIRE n.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_sim IF NOT EXISTS FOR (s:SIM) REQUIRE s.entity_id IS UNIQUE;

// Root Nodes
CREATE CONSTRAINT unique_case IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE;
CREATE CONSTRAINT unique_fir IF NOT EXISTS FOR (f:FIR) REQUIRE f.fir_id IS UNIQUE;

// ------------------------------------------------------------------------------
// 2. IDEMPOTENCY / SEQUENCE GUARDS
// ------------------------------------------------------------------------------
CREATE INDEX index_person_seq IF NOT EXISTS FOR (p:Person) ON (p.last_seq_no);
CREATE INDEX index_identity_seq IF NOT EXISTS FOR (i:Identity) ON (i.last_seq_no);
CREATE INDEX index_phonenumber_seq IF NOT EXISTS FOR (ph:PhoneNumber) ON (ph.last_seq_no);
CREATE INDEX index_device_seq IF NOT EXISTS FOR (d:Device) ON (d.last_seq_no);
CREATE INDEX index_vehicle_seq IF NOT EXISTS FOR (v:Vehicle) ON (v.last_seq_no);
CREATE INDEX index_financial_account_seq IF NOT EXISTS FOR (a:FinancialAccount) ON (a.last_seq_no);
CREATE INDEX index_property_seq IF NOT EXISTS FOR (pr:Property) ON (pr.last_seq_no);
CREATE INDEX index_location_seq IF NOT EXISTS FOR (l:Location) ON (l.last_seq_no);
CREATE INDEX index_organization_seq IF NOT EXISTS FOR (o:Organization) ON (o.last_seq_no);
CREATE INDEX index_network_seq IF NOT EXISTS FOR (n:Network) ON (n.last_seq_no);
CREATE INDEX index_sim_seq IF NOT EXISTS FOR (s:SIM) ON (s.last_seq_no);
CREATE INDEX index_case_seq IF NOT EXISTS FOR (c:Case) ON (c.last_seq_no);
CREATE INDEX index_fir_seq IF NOT EXISTS FOR (f:FIR) ON (f.last_seq_no);

// ------------------------------------------------------------------------------
// 3. SEARCH INDEXES (Optimizes queries and aggregations)
// ------------------------------------------------------------------------------

// Person lookups
CREATE INDEX index_person_name IF NOT EXISTS FOR (p:Person) ON (p.primary_name);
CREATE INDEX index_person_type IF NOT EXISTS FOR (p:Person) ON (p.person_type);
CREATE INDEX index_identity_value IF NOT EXISTS FOR (i:Identity) ON (i.value);

// Identifiers
CREATE INDEX index_phonenumber_number IF NOT EXISTS FOR (ph:PhoneNumber) ON (ph.number);
CREATE INDEX index_device_imei IF NOT EXISTS FOR (d:Device) ON (d.imei);
CREATE INDEX index_vehicle_registration IF NOT EXISTS FOR (v:Vehicle) ON (v.registration_number);
CREATE INDEX index_financialaccount_id IF NOT EXISTS FOR (a:FinancialAccount) ON (a.account_identifier);

// Legal / Case
CREATE INDEX index_fir_number IF NOT EXISTS FOR (f:FIR) ON (f.fir_number);
CREATE INDEX index_case_number IF NOT EXISTS FOR (c:Case) ON (c.case_number);

// Organizations & Networks
CREATE INDEX index_organization_name IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX index_network_name IF NOT EXISTS FOR (n:Network) ON (n.name);

// ------------------------------------------------------------------------------
// 4. FULL-TEXT INDEXES (For fuzzy searching across text properties)
// ------------------------------------------------------------------------------

CREATE FULLTEXT INDEX fti_person_names IF NOT EXISTS FOR (n:Person|Identity) ON EACH [n.primary_name, n.value];
CREATE FULLTEXT INDEX fti_locations IF NOT EXISTS FOR (l:Location) ON EACH [l.name, l.full_text, l.city];
CREATE FULLTEXT INDEX fti_organizations IF NOT EXISTS FOR (o:Organization) ON EACH [o.name];

// ------------------------------------------------------------------------------
// 5. EPISTEMIC MODEL CONSTRAINTS & INDEXES (Phase 7 Step 6)
// ------------------------------------------------------------------------------
CREATE CONSTRAINT unique_event IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE;
CREATE CONSTRAINT unique_assertion IF NOT EXISTS FOR (a:Assertion) REQUIRE a.assertion_id IS UNIQUE;
CREATE CONSTRAINT unique_hypothesis IF NOT EXISTS FOR (h:Hypothesis) REQUIRE h.hypothesis_id IS UNIQUE;
CREATE CONSTRAINT unique_lead IF NOT EXISTS FOR (l:Lead) REQUIRE l.lead_id IS UNIQUE;

CREATE INDEX index_event_seq IF NOT EXISTS FOR (e:Event) ON (e.last_seq_no);
CREATE INDEX index_assertion_seq IF NOT EXISTS FOR (a:Assertion) ON (a.last_seq_no);
CREATE INDEX index_hypothesis_seq IF NOT EXISTS FOR (h:Hypothesis) ON (h.last_seq_no);
CREATE INDEX index_lead_seq IF NOT EXISTS FOR (l:Lead) ON (l.last_seq_no);

// ==============================================================================
// CIVIX Platform — Neo4j Cypher Schema (Intelligence Engine)
// Derived from implementation_plan.md
// ==============================================================================

// ------------------------------------------------------------------------------
// 1. UNIQUENESS CONSTRAINTS (Ensures no duplicate entities are created)
// ------------------------------------------------------------------------------

CREATE CONSTRAINT unique_person IF NOT EXISTS FOR (p:Person) REQUIRE p.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_identity IF NOT EXISTS FOR (i:Identity) REQUIRE i.identity_id IS UNIQUE;
CREATE CONSTRAINT unique_phonenumber IF NOT EXISTS FOR (ph:PhoneNumber) REQUIRE ph.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_device IF NOT EXISTS FOR (d:Device) REQUIRE d.device_id IS UNIQUE;
CREATE CONSTRAINT unique_vehicle IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_financial_account IF NOT EXISTS FOR (a:FinancialAccount) REQUIRE a.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_property IF NOT EXISTS FOR (pr:Property) REQUIRE pr.property_id IS UNIQUE;
CREATE CONSTRAINT unique_location IF NOT EXISTS FOR (l:Location) REQUIRE l.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_address IF NOT EXISTS FOR (ad:Address) REQUIRE ad.address_id IS UNIQUE;
CREATE CONSTRAINT unique_organization IF NOT EXISTS FOR (o:Organization) REQUIRE o.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_network IF NOT EXISTS FOR (n:Network) REQUIRE n.network_id IS UNIQUE;
CREATE CONSTRAINT unique_case IF NOT EXISTS FOR (c:Case) REQUIRE c.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_fir IF NOT EXISTS FOR (f:FIR) REQUIRE f.entity_id IS UNIQUE;
CREATE CONSTRAINT unique_offence IF NOT EXISTS FOR (off:Offence) REQUIRE off.offence_id IS UNIQUE;
CREATE CONSTRAINT unique_document IF NOT EXISTS FOR (doc:Document) REQUIRE doc.document_id IS UNIQUE;
CREATE CONSTRAINT unique_event IF NOT EXISTS FOR (e:Event) REQUIRE e.event_id IS UNIQUE;
CREATE CONSTRAINT unique_anomaly_signal IF NOT EXISTS FOR (asig:AnomalySignal) REQUIRE asig.signal_id IS UNIQUE;

// ------------------------------------------------------------------------------
// 2. SEARCH INDEXES (Optimizes queries and aggregations)
// ------------------------------------------------------------------------------

// Person lookups
CREATE INDEX index_person_name IF NOT EXISTS FOR (p:Person) ON (p.primary_name);
CREATE INDEX index_person_type IF NOT EXISTS FOR (p:Person) ON (p.person_type);
CREATE INDEX index_identity_value IF NOT EXISTS FOR (i:Identity) ON (i.value);

// Identifiers
CREATE INDEX index_phonenumber_number IF NOT EXISTS FOR (ph:PhoneNumber) ON (ph.number);
CREATE INDEX index_device_imei IF NOT EXISTS FOR (d:Device) ON (d.imei);
CREATE INDEX index_vehicle_registration IF NOT EXISTS FOR (v:Vehicle) ON (v.registration_number);
CREATE INDEX index_property_registration IF NOT EXISTS FOR (pr:Property) ON (pr.registration_id);
CREATE INDEX index_financialaccount_id IF NOT EXISTS FOR (a:FinancialAccount) ON (a.account_identifier);

// Legal / Case
CREATE INDEX index_fir_number IF NOT EXISTS FOR (f:FIR) ON (f.fir_number);
CREATE INDEX index_case_number IF NOT EXISTS FOR (c:Case) ON (c.case_number);

// Events & Anomalies
CREATE INDEX index_event_timestamp IF NOT EXISTS FOR (e:Event) ON (e.timestamp);
CREATE INDEX index_event_type IF NOT EXISTS FOR (e:Event) ON (e.event_type);
CREATE INDEX index_anomalysignal_type IF NOT EXISTS FOR (asig:AnomalySignal) ON (asig.signal_type);
CREATE INDEX index_anomalysignal_timestamp IF NOT EXISTS FOR (asig:AnomalySignal) ON (asig.timestamp);

// Organizations & Networks
CREATE INDEX index_organization_name IF NOT EXISTS FOR (o:Organization) ON (o.name);
CREATE INDEX index_network_name IF NOT EXISTS FOR (n:Network) ON (n.name);

// ------------------------------------------------------------------------------
// 3. FULL-TEXT INDEXES (For fuzzy searching across text properties)
// ------------------------------------------------------------------------------

CREATE FULLTEXT INDEX fti_person_names IF NOT EXISTS FOR (n:Person|Identity) ON EACH [n.primary_name, n.value];
CREATE FULLTEXT INDEX fti_locations IF NOT EXISTS FOR (l:Location|Address) ON EACH [l.name, l.full_text, l.city];
CREATE FULLTEXT INDEX fti_organizations IF NOT EXISTS FOR (o:Organization) ON EACH [o.name];

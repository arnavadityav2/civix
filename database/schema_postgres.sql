-- ==============================================================================
-- CIVIX Platform — PostgreSQL Schema (System of Record)
-- Derived from implementation_plan.md
-- ==============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- 1. Authentication & Authorization
-- ==============================================================================

CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==============================================================================
-- 2. Data Ingestion & Provenance
-- ==============================================================================

CREATE TABLE ingestion_jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50), -- e.g., 'CDR_IMPORT', 'FIR_IMPORT'
    status VARCHAR(20),   -- 'RUNNING', 'COMPLETED', 'FAILED'
    records_processed INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_log TEXT
);

CREATE TABLE source_documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_type VARCHAR(50) NOT NULL, -- e.g., 'FIR', 'SurveillanceReport', 'CDRDump'
    title VARCHAR(255) NOT NULL,
    content_text TEXT,
    file_reference VARCHAR(500),
    classification VARCHAR(50) NOT NULL DEFAULT 'Unclassified',
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ingested_by UUID REFERENCES users(user_id)
);

CREATE TABLE source_records (
    record_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES source_documents(document_id),
    record_type VARCHAR(50) NOT NULL, -- e.g., 'FIR', 'CDR', 'FinancialTransaction'
    source_identifier VARCHAR(100),   -- e.g., 'CDR-00982'
    raw_data JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_source_records_type ON source_records(record_type);
CREATE INDEX idx_source_records_data ON source_records USING GIN (raw_data);

-- ==============================================================================
-- 3. Entity Resolution & Master Data Management (MDM)
-- ==============================================================================

CREATE TABLE entity_master (
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(50) NOT NULL, -- 'Person', 'Vehicle', 'Location', etc.
    primary_name VARCHAR(255),
    status VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_entity_master_type ON entity_master(entity_type);

CREATE TABLE entity_raw_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_entity_id UUID REFERENCES entity_master(entity_id),
    raw_record_id UUID REFERENCES source_records(record_id),
    match_confidence DECIMAL(5,4),
    method VARCHAR(50), -- 'DirectFromSource', 'RuleBased', 'HumanVerified'
    mapped_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_entity_raw_mapping_canonical ON entity_raw_mapping(canonical_entity_id);
CREATE INDEX idx_entity_raw_mapping_raw ON entity_raw_mapping(raw_record_id);

CREATE TABLE entity_resolution_decisions (
    decision_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    canonical_entity_id UUID REFERENCES entity_master(entity_id),
    candidate_raw_record_id UUID REFERENCES source_records(record_id),
    decision VARCHAR(50) NOT NULL, -- 'MERGE', 'REJECT', 'DEFER'
    confidence_score DECIMAL(5,4),
    decided_by UUID REFERENCES users(user_id),
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- ==============================================================================
-- 4. Application State (Investigative Workflow)
-- ==============================================================================

CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type VARCHAR(100) NOT NULL, -- e.g., 'CommunicationBurst', 'FinancialSpike'
    severity VARCHAR(20) NOT NULL,    -- 'Low', 'Medium', 'High', 'Critical'
    status VARCHAR(20) DEFAULT 'NEW', -- 'NEW', 'IN_PROGRESS', 'CLOSED', 'DISMISSED'
    summary TEXT,
    evidence_payload JSONB,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_to UUID REFERENCES users(user_id)
);

CREATE TABLE case_notes (
    note_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID, -- UUID of the entity, case, or alert this note refers to
    author_id UUID REFERENCES users(user_id),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE saved_searches (
    search_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id),
    title VARCHAR(255) NOT NULL,
    query_payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

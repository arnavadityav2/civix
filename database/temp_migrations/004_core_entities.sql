-- =============================================================================
-- CIVIX Platform — Migration 004: Core Entity Model
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 05, 06
--            ADR-001: Universal Entity Supertype
--            ADR-005: No is_criminal on Person (INV-17)
--            BLK-03/ADR-014: extraction_id removed from source_identity
--            BLK-16/ADR-018: Entity tombstoning — no physical DELETE
--            BLK-09/ADR-021: No entity FKs on event table
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- civix.entity — Universal Supertype (ADR-001)
-- ALL entity subtypes share this PK.
-- ---------------------------------------------------------------------------
CREATE TABLE civix.entity (
    entity_id       UUID                   PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type     civix.entity_type_enum NOT NULL,
    -- BLK-16/ADR-018: Tombstoning — physical DELETE is FORBIDDEN via trigger (see 010_triggers.sql)
    -- Lifecycle: ACTIVE → RESTRICTED → TOMBSTONED
    visibility_status TEXT                 NOT NULL DEFAULT 'ACTIVE',
    -- Values: ACTIVE, RESTRICTED, TOMBSTONED
    created_at      TIMESTAMPTZ            NOT NULL DEFAULT now(),
    created_by      UUID                   NULL REFERENCES civix.civix_user(user_id)
);

COMMENT ON TABLE civix.entity IS
    'Universal entity supertype. ALL entity subtypes share this PK via table inheritance pattern (entity_id is PK AND FK to here). Physical deletion is FORBIDDEN — use visibility_status=TOMBSTONED. ADR-001, BLK-16.';
COMMENT ON COLUMN civix.entity.visibility_status IS
    'ACTIVE | RESTRICTED | TOMBSTONED. Tombstoning preserves all FKs while removing from analytical views. Physical DELETE is rejected by trigger. BLK-16/ADR-018.';

-- ---------------------------------------------------------------------------
-- civix.source_identity — Subtype
-- Raw identifier from a source record. raw_identifier is IMMUTABLE.
-- Authority: BLK-03/ADR-014 — NO extraction_id column
-- ---------------------------------------------------------------------------
CREATE TABLE civix.source_identity (
    entity_id           UUID                         PRIMARY KEY REFERENCES civix.entity(entity_id),
    raw_identifier      TEXT                         NOT NULL,   -- IMMUTABLE after creation (INV-03)
    identifier_type     civix.source_identity_type_enum NOT NULL,
    source_record_id    UUID                         NULL REFERENCES civix.source_record(source_record_id),
    -- extraction_id REMOVED (BLK-03/ADR-014). AI-derived identities link via civix.provenance.
    observed_at         TIMESTAMPTZ                  NOT NULL,
    tx_start            TIMESTAMPTZ                  NOT NULL DEFAULT now(),
    tx_end              TIMESTAMPTZ                  NULL
);
-- INVARIANT (INV-03): raw_identifier is IMMUTABLE. Corrections insert a new source_identity row.
-- INVARIANT: extraction_id column does NOT exist here (ADR-014). See civix.provenance for AI linkage.

COMMENT ON TABLE civix.source_identity IS
    'Raw identifier from a source record. Immutable. AI-derived identities linked via civix.provenance. extraction_id removed — ADR-014.';

-- ---------------------------------------------------------------------------
-- civix.person — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.person (
    entity_id      UUID        PRIMARY KEY REFERENCES civix.entity(entity_id),
    display_name   TEXT        NOT NULL,
    date_of_birth  DATE        NULL,
    gender         TEXT        NULL,
    -- Values: MALE, FEMALE, OTHER, UNDISCLOSED
    nationality    CHAR(3)     NULL,   -- ISO 3166-1 alpha-3
    is_deceased    BOOLEAN     NOT NULL DEFAULT FALSE,
    deceased_at    DATE        NULL,
    notes          TEXT        NULL
    -- NO is_criminal, is_suspect, criminal_record_count (ADR-005, INV-17)
    -- Criminal status is expressed via case_entity_role
);

COMMENT ON TABLE civix.person IS
    'Canonical person entity. PROHIBITED columns: is_criminal, is_suspect, criminal_record_count. These are hypotheses, not facts. ADR-005, INV-17.';

-- ---------------------------------------------------------------------------
-- civix.person_alias — Bitemporal
-- ---------------------------------------------------------------------------
CREATE TABLE civix.person_alias (
    alias_id        UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID    NOT NULL REFERENCES civix.person(entity_id),
    alias_value     TEXT    NOT NULL,
    alias_type      TEXT    NOT NULL,
    -- Values: AKA, NICKNAME, MAIDEN_NAME, PROFESSIONAL_NAME, ALIAS_CRIMINAL, OTHER
    source_record_id UUID   NULL REFERENCES civix.source_record(source_record_id),
    valid_from      DATE    NULL,
    valid_to        DATE    NULL,
    tx_start        TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_person_alias UNIQUE (person_id, alias_value, alias_type)
);

-- ---------------------------------------------------------------------------
-- civix.phone_number — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.phone_number (
    entity_id    UUID        PRIMARY KEY REFERENCES civix.entity(entity_id),
    msisdn       VARCHAR(15) NOT NULL UNIQUE,   -- E.164 format without '+'
    country_code CHAR(3)     NOT NULL DEFAULT 'IND',
    operator     TEXT        NULL,
    number_type  TEXT        NULL   -- MOBILE, LANDLINE, VOIP, UNKNOWN
);

-- ---------------------------------------------------------------------------
-- civix.sim — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.sim (
    entity_id        UUID        PRIMARY KEY REFERENCES civix.entity(entity_id),
    iccid            VARCHAR(22) NOT NULL UNIQUE,
    imsi             VARCHAR(15) UNIQUE NULL,
    issuing_operator TEXT        NULL
);

-- ---------------------------------------------------------------------------
-- civix.device — Subtype
-- IMEI is nullable: CDRs may contain UNKNOWN-IMEI → source_identity, not device row
-- ---------------------------------------------------------------------------
CREATE TABLE civix.device (
    entity_id    UUID        PRIMARY KEY REFERENCES civix.entity(entity_id),
    imei         VARCHAR(17) UNIQUE NULL,   -- Nullable: UNKNOWN-IMEI → source_identity
    mac_address  VARCHAR(17) UNIQUE NULL,
    device_type  TEXT        NOT NULL,     -- SMARTPHONE, TABLET, FEATURE_PHONE, OTHER
    manufacturer TEXT        NULL,
    model        TEXT        NULL
);

COMMENT ON COLUMN civix.device.imei IS
    'Nullable. CDRs with UNKNOWN-IMEI produce a source_identity row, not a device row. See ingestion rules.';

-- ---------------------------------------------------------------------------
-- civix.vehicle — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.vehicle (
    entity_id           UUID    PRIMARY KEY REFERENCES civix.entity(entity_id),
    registration_number TEXT    NOT NULL UNIQUE,
    vin                 TEXT    UNIQUE NULL,
    make                TEXT    NULL,
    model               TEXT    NULL,
    color               TEXT    NULL,
    vehicle_type        TEXT    NOT NULL,  -- CAR, TRUCK, MOTORCYCLE, AUTO_RICKSHAW, OTHER
    registration_year   INT     NULL
);

-- ---------------------------------------------------------------------------
-- civix.property — Subtype
-- Uses PostGIS GEOMETRY for boundary representation
-- ---------------------------------------------------------------------------
CREATE TABLE civix.property (
    entity_id         UUID             PRIMARY KEY REFERENCES civix.entity(entity_id),
    property_ref      TEXT             NOT NULL,       -- Khasra number, plot ID
    property_type     TEXT             NOT NULL,       -- RESIDENTIAL, COMMERCIAL, AGRICULTURAL, OTHER
    area_sqm          DECIMAL          NULL,
    description       TEXT             NULL,
    boundary_geometry JSONB NULL     -- PostGIS spatial boundary
);

-- ---------------------------------------------------------------------------
-- civix.financial_account — Subtype
-- Unresolvable org-name account IDs (e.g. "Network Beta" from transactions.csv)
-- → source_identity rows, NOT financial_account rows
-- ---------------------------------------------------------------------------
CREATE TABLE civix.financial_account (
    entity_id    UUID    PRIMARY KEY REFERENCES civix.entity(entity_id),
    masked_number TEXT   NOT NULL,        -- e.g. "****8877"
    account_type  TEXT   NOT NULL,        -- SAVINGS, CURRENT, FIXED_DEPOSIT, WALLET
    bank_name     TEXT   NULL,
    ifsc_code     CHAR(11) NULL,
    currency      CHAR(3)  NOT NULL DEFAULT 'INR'
);

-- ---------------------------------------------------------------------------
-- civix.organization — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.organization (
    entity_id          UUID    PRIMARY KEY REFERENCES civix.entity(entity_id),
    legal_name         TEXT    NOT NULL,
    org_type           TEXT    NOT NULL,   -- NGO, COMPANY, GOVT, CRIMINAL_NETWORK, OTHER
    registration_number TEXT   NULL,
    incorporation_date DATE    NULL,
    jurisdiction       TEXT    NULL
);

-- ---------------------------------------------------------------------------
-- civix.network — Subtype
-- ---------------------------------------------------------------------------
CREATE TABLE civix.network (
    entity_id    UUID    PRIMARY KEY REFERENCES civix.entity(entity_id),
    network_name TEXT    NOT NULL,
    network_type TEXT    NOT NULL,   -- CRIMINAL, FINANCIAL, COMMUNICATION, OTHER
    notes        TEXT    NULL
);
-- INVARIANT (INV-16): network_type = 'CRIMINAL' is investigative categorization.
-- It is NOT proof of member guilt. Members belong via event_participant or assertion.

-- ---------------------------------------------------------------------------
-- civix.location — Subtype (PostGIS)
-- Authority: ADR-009, INV-19 — Cell tower centroid ≠ user position
-- ---------------------------------------------------------------------------
CREATE TABLE civix.location (
    entity_id                UUID                      PRIMARY KEY REFERENCES civix.entity(entity_id),
    location_name            TEXT                      NULL,
    geometry                 JSONB  NOT NULL,
    -- Supports Point (EXACT_POINT, ESTIMATED_POINT), Polygon (CELL_SECTOR, GEOFENCE),
    -- LineString (ROUTE_LINESTRING)
    location_type            civix.location_type_enum  NOT NULL,
    uncertainty_radius_meters FLOAT                    NULL,   -- For ESTIMATED_POINT
    altitude_meters          FLOAT                     NULL,
    azimuth_degrees          FLOAT                     NULL,   -- Cell sector direction
    beamwidth_degrees        FLOAT                     NULL,   -- Cell sector angular width
    source_record_id         UUID                      NULL REFERENCES civix.source_record(source_record_id)
);
-- INVARIANT (INV-19): CELL_SECTOR_POLYGON locations represent coverage areas.
-- A device pinging a tower does NOT imply the person was at the tower centroid.
-- Observation is: "device was within this polygon" with uncertainty.

COMMENT ON COLUMN civix.location.geometry IS
    'PostGIS geometry. Cell towers use Polygon (CELL_SECTOR_POLYGON). Exact GPS uses Point. Never store cell tower centroid as person position. INV-19, ADR-009.';

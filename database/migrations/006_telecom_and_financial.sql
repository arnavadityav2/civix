-- =============================================================================
-- CIVIX Platform — Migration 006: Telecom & Financial Relationships
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §Migration 07, 08
--            BLK-10: Multi-hop bitemporal telecom model
--            BLK-11/ADR-021: Bitemporal financial account roles
--            INV-15: SIM physical constraints differ from person-use
--            ADR-009: GIST exclusion on temporal ranges
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- TELECOM RELATIONSHIPS
-- ---------------------------------------------------------------------------
-- Architecture: The telecom model distinguishes:
--   LEGAL/REGISTERED OWNERSHIP   → person_sim_ownership
--   PHYSICAL ASSIGNMENT (SIM↔Device) → sim_in_device
--   PHONE NUMBER ASSIGNMENT (SIM↔Number) → sim_number_assignment
--   OBSERVED USAGE (Person↔Device)  → person_device_use
-- These MUST NOT be collapsed into one-to-one relationships.
-- ---------------------------------------------------------------------------

-- civix.sim_number_assignment
-- Which SIM card carries which MSISDN at what time.
-- One MSISDN cannot be assigned to TWO SIMs simultaneously (telecom law).
-- Supports number recycling: same MSISDN can go to a different SIM later.
CREATE TABLE civix.sim_number_assignment (
    assignment_id    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_id           UUID        NOT NULL REFERENCES civix.sim(entity_id),
    phone_number_id  UUID        NOT NULL REFERENCES civix.phone_number(entity_id),
    valid_time       TSTZRANGE   NOT NULL,   -- [valid_from, valid_to)
    source_record_id UUID        NULL REFERENCES civix.source_record(source_record_id),
    tx_start         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- INVARIANT: One MSISDN → one SIM at any point in valid_time
    -- Allows number recycling over time (non-overlapping intervals for same phone_number_id)
    CONSTRAINT excl_sim_number_time
        EXCLUDE USING GIST (phone_number_id WITH =, valid_time WITH &&)
);

COMMENT ON TABLE civix.sim_number_assignment IS
    'Assigns a phone number (MSISDN) to a SIM card over a time interval. GIST exclusion prevents one MSISDN being on two SIMs simultaneously. Supports number recycling. ADR-009.';

-- civix.sim_in_device
-- Physical installation of a SIM card in a device.
-- One SIM cannot be in TWO devices simultaneously (physical law).
-- A dual-SIM device requires TWO sim_in_device rows (one per SIM slot).
CREATE TABLE civix.sim_in_device (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_id           UUID        NOT NULL REFERENCES civix.sim(entity_id),
    device_id        UUID        NOT NULL REFERENCES civix.device(entity_id),
    valid_time       TSTZRANGE   NOT NULL,
    tx_start         TIMESTAMPTZ NOT NULL DEFAULT now(),

    -- INVARIANT: One SIM → one device at any point in valid_time (physical law)
    -- INV-15: Different from person-use semantics
    CONSTRAINT excl_sim_in_device_time
        EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)
);

COMMENT ON TABLE civix.sim_in_device IS
    'Physical SIM-in-device assignment. GIST exclusion enforces one-device-per-SIM-at-a-time. Dual-SIM: two rows with different sim_id. INV-15.';

-- civix.person_sim_ownership
-- Legal/registered ownership of a SIM card by a person.
-- Does NOT imply the person was the user during any given call event.
CREATE TABLE civix.person_sim_ownership (
    ownership_id      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id         UUID        NOT NULL REFERENCES civix.person(entity_id),
    sim_id            UUID        NOT NULL REFERENCES civix.sim(entity_id),
    ownership_type    TEXT        NOT NULL DEFAULT 'REGISTERED',
    -- Values: REGISTERED, PURCHASED, TRANSFERRED, REPORTED_STOLEN
    valid_time        TSTZRANGE   NOT NULL,
    source_record_id  UUID        NULL REFERENCES civix.source_record(source_record_id),
    tx_start          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE civix.person_sim_ownership IS
    'Legal/registered SIM ownership. Separate from physical usage. A person may own a SIM that someone else used. BLK-10.';

-- civix.person_device_use
-- Observed or reported USAGE of a device by a person.
-- CRITICAL: NO exclusivity constraint — multiple people may use the same device.
-- (Shared phones, burner phones, family devices)
CREATE TABLE civix.person_device_use (
    use_id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id         UUID        NOT NULL REFERENCES civix.person(entity_id),
    device_id         UUID        NOT NULL REFERENCES civix.device(entity_id),
    usage_type        TEXT        NOT NULL DEFAULT 'PRIMARY',
    -- Values: PRIMARY, SHARED, HISTORICAL, OBSERVED, INFERRED
    valid_time        TSTZRANGE   NOT NULL,
    source_record_id  UUID        NULL REFERENCES civix.source_record(source_record_id),
    tx_start          TIMESTAMPTZ NOT NULL DEFAULT now()
    -- NO exclusion constraint: multiple persons may use same device simultaneously
    -- This is intentional — shared/family/burner phones are a common investigative scenario.
);

COMMENT ON TABLE civix.person_device_use IS
    'Observed device usage by a person. NO exclusivity constraint — multiple people may use same device. Shared/family/burner phones supported. BLK-10.';

-- ---------------------------------------------------------------------------
-- FINANCIAL RELATIONSHIPS
-- ---------------------------------------------------------------------------

-- civix.account_holder (BLK-11/ADR-021 — fully bitemporal)
-- Links a person/org to a financial account with a specific role.
-- CRITICAL: Role must NEVER be inferred from transaction initiation.
-- An authorized signatory is NOT an account owner.
CREATE TABLE civix.account_holder (
    holder_id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id             UUID        NOT NULL REFERENCES civix.financial_account(entity_id),
    holder_entity_id       UUID        NOT NULL REFERENCES civix.entity(entity_id),
    -- holder_entity_id may point to PERSON or ORGANIZATION (via entity supertype)
    holder_role            TEXT        NOT NULL,
    -- Canonical vocabulary (BLK-11):
    --   PRIMARY_OWNER       — sole owner; full legal authority
    --   JOINT_OWNER         — co-owner with equal or fractional rights
    --   AUTHORIZED_SIGNATORY— can transact but does NOT own
    --   BENEFICIAL_OWNER    — ultimate economic beneficiary (may be different from legal owner)
    --   POA                 — power of attorney; transact on behalf of owner
    --   NOMINEE             — holds account in trust for beneficiary
    --   CORPORATE_DIRECTOR  — authorized officer of an organization-owned account
    ownership_percentage   DECIMAL(5,2) NULL CHECK (ownership_percentage BETWEEN 0.0 AND 100.0),
    -- NULL for non-ownership roles (AUTHORIZED_SIGNATORY, POA, etc.)
    valid_time             TSTZRANGE    NOT NULL,
    source_record_id       UUID         NULL REFERENCES civix.source_record(source_record_id),
    tx_start               TIMESTAMPTZ  NOT NULL DEFAULT now(),
    tx_end                 TIMESTAMPTZ  NULL   -- NULL = currently active
);
-- INVARIANT: holder_role = 'AUTHORIZED_SIGNATORY' does NOT make the entity an owner.
-- Transactions must not create OWNS assertion for signatories.
-- INV-16 equivalent for finance: account access ≠ account ownership.

COMMENT ON TABLE civix.account_holder IS
    'Account ownership and authorization model. Bitemporal. AUTHORIZED_SIGNATORY ≠ owner. Prevents false ownership assertions from transaction events. BLK-11, ADR-021.';

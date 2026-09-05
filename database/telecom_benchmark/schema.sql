-- ============================================================
-- CIVIX 2.0 — TELECOM BENCHMARK SCHEMA
-- ============================================================
-- PURPOSE: Isolated synthetic telecom benchmark schema.
--          NO foreign keys pointing to civix.* schema.
--          All data is synthetic. Provenance fields mandatory.
-- AUTHOR:  CIVIX Telecom Benchmark Generator v1
-- WARNING: DO NOT modify civix.* schema. This file is additive only.
-- ============================================================

-- Safety check: Ensure we are on the expected database
-- (enforced in Python as well; this comment is documentary)

CREATE SCHEMA IF NOT EXISTS civix_telecom_benchmark;

-- ─── GENERATION RUNS ────────────────────────────────────────────────────────
-- Tracks every generator execution. All other tables reference generation_run_id.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.generation_run (
    generation_run_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    seed                INTEGER NOT NULL,
    tier                INTEGER NOT NULL DEFAULT 1,
    generator_version   TEXT NOT NULL DEFAULT 'telecom-benchmark-v1',
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    notes               TEXT
);

-- ─── BENCHMARK CASES ─────────────────────────────────────────────────────────
-- Each row represents a synthetic investigative scenario.
-- case_number MUST start with BENCH- and MUST NOT match any civix.investigative_case row.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_case (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number         TEXT NOT NULL UNIQUE,  -- e.g. BENCH-TELECOM-001
    title               TEXT NOT NULL,
    description         TEXT,
    scenario_type       TEXT NOT NULL,  -- SUSPECT_MOVEMENT | COMMON_TOWER_OVERLAP | SIM_IMEI_REUSE | CROSS_CASE_LINK | MIXED
    severity            TEXT NOT NULL DEFAULT 'HIGH',
    start_time          TIMESTAMPTZ,
    end_time            TIMESTAMPTZ,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_bench_case_number CHECK (case_number LIKE 'BENCH-%')
);

-- ─── BENCHMARK TOWERS ────────────────────────────────────────────────────────
-- Delhi NCR synthetic cell towers. No cross-schema references.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_tower (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tower_code          TEXT NOT NULL UNIQUE,  -- e.g. TOWER-DW-01
    name                TEXT NOT NULL,
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    area                TEXT,  -- e.g. Dwarka, Rohini, Noida
    azimuth_degrees     INTEGER,
    coverage_radius_m   INTEGER NOT NULL DEFAULT 500,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── BENCHMARK PHONES ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_phone (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    msisdn              TEXT NOT NULL UNIQUE,  -- e.g. BENCH-9811XXXXXX
    operator            TEXT,
    circle              TEXT DEFAULT 'Delhi',
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── BENCHMARK DEVICES ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_device (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    imei                TEXT NOT NULL UNIQUE,  -- e.g. BENCH-IMEI-001
    manufacturer        TEXT,
    model               TEXT,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── BENCHMARK SIMs ──────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_sim (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    iccid               TEXT NOT NULL UNIQUE,  -- e.g. BENCH-SIM-001
    imsi                TEXT UNIQUE,
    issuing_operator    TEXT,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── SIM ↔ DEVICE LINKS (SIM SWAP HISTORY) ────────────────────────────────
-- Tracks which SIM was in which device during a time window.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_sim_device_link (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sim_id              UUID NOT NULL REFERENCES civix_telecom_benchmark.benchmark_sim(id),
    device_id           UUID NOT NULL REFERENCES civix_telecom_benchmark.benchmark_device(id),
    phone_id            UUID REFERENCES civix_telecom_benchmark.benchmark_phone(id),
    valid_from          TIMESTAMPTZ NOT NULL,
    valid_to            TIMESTAMPTZ,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id)
);

-- ─── BENCHMARK EVENTS ────────────────────────────────────────────────────────
-- The core telecom event records.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_event (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id             UUID NOT NULL REFERENCES civix_telecom_benchmark.benchmark_case(id),
    event_type          TEXT NOT NULL,  -- CALL | DEVICE_PING | MESSAGE
    occurred_at         TIMESTAMPTZ NOT NULL,
    duration_seconds    INTEGER,
    caller_phone_id     UUID REFERENCES civix_telecom_benchmark.benchmark_phone(id),
    callee_phone_id     UUID REFERENCES civix_telecom_benchmark.benchmark_phone(id),
    subject_phone_id    UUID REFERENCES civix_telecom_benchmark.benchmark_phone(id),
    device_id           UUID REFERENCES civix_telecom_benchmark.benchmark_device(id),
    sim_id              UUID REFERENCES civix_telecom_benchmark.benchmark_sim(id),
    tower_id            UUID REFERENCES civix_telecom_benchmark.benchmark_tower(id),
    description         TEXT,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── CROSS-CASE ENTITY LINKS ──────────────────────────────────────────────
-- Tracks which benchmark phones/devices appear across multiple benchmark cases.

CREATE TABLE IF NOT EXISTS civix_telecom_benchmark.benchmark_cross_case_link (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_a_id           UUID NOT NULL REFERENCES civix_telecom_benchmark.benchmark_case(id),
    case_b_id           UUID NOT NULL REFERENCES civix_telecom_benchmark.benchmark_case(id),
    entity_type         TEXT NOT NULL,  -- PHONE | DEVICE | SIM
    entity_id           UUID NOT NULL,  -- FK to phone/device/sim
    link_note           TEXT,
    synthetic_flag      BOOLEAN NOT NULL DEFAULT TRUE,
    provenance          TEXT NOT NULL DEFAULT 'SYNTHETIC_TELECOM_BENCHMARK',
    generation_run_id   UUID NOT NULL REFERENCES civix_telecom_benchmark.generation_run(generation_run_id),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── INDEXES ─────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_bench_event_case    ON civix_telecom_benchmark.benchmark_event(case_id);
CREATE INDEX IF NOT EXISTS idx_bench_event_tower   ON civix_telecom_benchmark.benchmark_event(tower_id);
CREATE INDEX IF NOT EXISTS idx_bench_event_time    ON civix_telecom_benchmark.benchmark_event(occurred_at);
CREATE INDEX IF NOT EXISTS idx_bench_event_caller  ON civix_telecom_benchmark.benchmark_event(caller_phone_id);
CREATE INDEX IF NOT EXISTS idx_bench_event_callee  ON civix_telecom_benchmark.benchmark_event(callee_phone_id);
CREATE INDEX IF NOT EXISTS idx_bench_event_subject ON civix_telecom_benchmark.benchmark_event(subject_phone_id);
CREATE INDEX IF NOT EXISTS idx_bench_event_device  ON civix_telecom_benchmark.benchmark_event(device_id);
CREATE INDEX IF NOT EXISTS idx_bench_sdl_sim       ON civix_telecom_benchmark.benchmark_sim_device_link(sim_id);
CREATE INDEX IF NOT EXISTS idx_bench_sdl_device    ON civix_telecom_benchmark.benchmark_sim_device_link(device_id);

-- ============================================================
-- END SCHEMA
-- ============================================================

import psycopg2

sql = """
SET search_path TO civix, public;

CREATE TABLE IF NOT EXISTS civix.evidence_generation_manifest (
    manifest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL,
    source_record_id UUID NOT NULL,
    evidence_id_str VARCHAR(50) NOT NULL UNIQUE,
    evidence_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    prompt TEXT NOT NULL,
    expected_mime_type VARCHAR(100) NOT NULL,
    generation_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    artifact_id UUID NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE civix.evidence_generation_manifest IS
    'Tracks evidence generation intent prior to physical artifact creation and hashing.';
"""

print("Running migration 033...")
try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("Migration successful.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()

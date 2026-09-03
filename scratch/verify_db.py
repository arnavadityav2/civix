import psycopg2

DB_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"

artifact_ids = [
    "68d2b7b7-27dc-4828-b625-fbea4f77d311",
    "aca3265b-bfa5-4a09-9390-af1b4bedc675",
    "bae08f07-369f-414f-8613-6a436774ece4",
    "798d0cdb-8008-4989-83dd-210c47c232a7",
    "4ee0fded-79ef-436c-9887-c8d11f7ba279",
    "03913943-e19b-4753-81c3-2c64a4855514",
    "12a8ead4-32aa-453c-8234-587f7819c3c4",
    "68ff37c3-49bf-4d0c-a9ee-c593d87bfc97",
    "5b74b2d3-8914-446d-bfff-965fb1aab721",
    "f6fbbfd3-a8d4-493b-a6bc-c55d9e44b5d3"
]

def report(name, passed, extra=""):
    if passed: print(f"  [PASS] {name} {extra}")
    else: print(f"  [FAIL] {name} {extra}")

conn = psycopg2.connect(DB_DSN)
cur = conn.cursor()

# Get instance_ids
cur.execute("SELECT instance_id FROM civix.evidence_instance WHERE artifact_id = ANY(%s::uuid[])", (artifact_ids,))
instance_ids = [r[0] for r in cur.fetchall()]
if not instance_ids:
    print("No instance IDs found!")
    exit(1)

# Check entities
cur.execute("SELECT count(DISTINCT derived_id) FROM civix.provenance WHERE derived_type != 'ASSERTION' AND source_type = 'EXTRACTION' AND source_id IN (SELECT extraction_id FROM civix.extraction WHERE instance_id = ANY(%s::uuid[]))", (instance_ids,))
entity_count = cur.fetchone()[0]
report("Entities Persisted", entity_count > 10, f"(Total: {entity_count})")

# Check assertions
cur.execute("SELECT count(DISTINCT derived_id) FROM civix.provenance WHERE derived_type = 'ASSERTION' AND source_type = 'EXTRACTION' AND source_id IN (SELECT extraction_id FROM civix.extraction WHERE instance_id = ANY(%s::uuid[]))", (instance_ids,))
assertion_count = cur.fetchone()[0]
report("Assertions Persisted", assertion_count > 5, f"(Total: {assertion_count})")

# Check provenance
cur.execute("SELECT count(*) FROM civix.provenance WHERE source_type = 'EXTRACTION' AND source_id IN (SELECT extraction_id FROM civix.extraction WHERE instance_id = ANY(%s::uuid[]))", (instance_ids,))
prov_count = cur.fetchone()[0]
report("Provenance Traces Persisted", prov_count > 20, f"(Total: {prov_count})")

# Check outbox (using case_id = b281ad86-1b43-458c-b751-fc44cb467823)
cur.execute("SELECT count(*) FROM civix.outbox WHERE entity_id IN (SELECT derived_id FROM civix.provenance WHERE source_type = 'EXTRACTION' AND source_id IN (SELECT extraction_id FROM civix.extraction WHERE instance_id = ANY(%s::uuid[])))", (instance_ids,))
outbox_count = cur.fetchone()[0]
report("Outbox Events Generated", outbox_count > 0, f"(Total: {outbox_count})")

def check_entity(label, search_text):
    cur.execute("""
        SELECT count(*) FROM civix.entity 
        WHERE entity_type = CAST(%s AS civix.entity_type_enum) AND (
            entity_id IN (SELECT entity_id FROM civix.person WHERE display_name ILIKE %s)
            OR entity_id IN (SELECT entity_id FROM civix.organization WHERE legal_name ILIKE %s)
            OR entity_id IN (SELECT entity_id FROM civix.vehicle WHERE registration_number ILIKE %s)
            OR entity_id IN (SELECT entity_id FROM civix.location WHERE location_name ILIKE %s)
        )
        AND entity_id IN (SELECT derived_id FROM civix.provenance WHERE source_type = 'EXTRACTION' AND source_id IN (SELECT extraction_id FROM civix.extraction WHERE instance_id = ANY(%s::uuid[])))
    """, (label, f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", f"%{search_text}%", instance_ids))
    count = cur.fetchone()[0]
    report(f"Found {label}: {search_text}", count > 0, f"({count} times)")

print("\\n--- EXTRACTION QUALITY AUDIT ---")
check_entity("PERSON", "Vikram")
check_entity("PERSON", "Neha")
check_entity("PERSON", "Rajat")
check_entity("ORGANIZATION", "Horizon")
check_entity("ORGANIZATION", "Zenith")
check_entity("VEHICLE", "HR-26")
check_entity("LOCATION", "Cyber Hub")

import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

# 1. Total table count
cur.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = 'civix';")
tbl_count = cur.fetchone()[0]

# 2. List all tables in civix schema
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' ORDER BY table_name;")
tables = [r[0] for r in cur.fetchall()]

# 3. Check person table columns (e.g. national_id, aadhar, passport, etc.)
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'person';")
person_cols = cur.fetchall()

# 4. Count of records in key entity tables
entity_counts = {}
key_tables = [
    'investigative_case', 'person', 'organization', 'vehicle', 
    'sim_card', 'mobile_device', 'bank_account', 'bank_transaction', 
    'location', 'event', 'cctv_camera', 'cdr_record', 
    'ip_address', 'property', 'hypothesis'
]

for t in key_tables:
    try:
        cur.execute(f"SELECT count(*) FROM civix.{t};")
        entity_counts[t] = cur.fetchone()[0]
    except Exception as e:
        conn.rollback()
        entity_counts[t] = f"Error: {e}"

print("==========================================")
print(f"Total Tables in Schema 'civix': {tbl_count}")
print("==========================================")
print("\nAll 52 Tables:")
for t in tables:
    print(f" - civix.{t}")

print("\n------------------------------------------")
print("Person Columns (Identities & IDs):")
for col in person_cols:
    print(f" - {col[0]} ({col[1]})")

print("\n------------------------------------------")
print("Entity Record Counts in civix_demo:")
for k, v in entity_counts.items():
    print(f" - {k}: {v}")

conn.close()

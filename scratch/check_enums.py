import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'case_status_enum';")
print("case_status_enum:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'case_priority_enum';")
print("case_priority_enum:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE typname = 'case_type_enum';")
print("case_type_enum:", [r[0] for r in cur.fetchall()])

conn.close()

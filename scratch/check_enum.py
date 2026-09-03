import psycopg
conn=psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur=conn.cursor()
cur.execute("SELECT e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid WHERE t.typname = 'case_entity_role_enum'")
print([r[0] for r in cur.fetchall()])

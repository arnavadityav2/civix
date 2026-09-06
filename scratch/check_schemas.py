import psycopg2
import os

conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
cur = conn.cursor()

cur.execute("SELECT schema_name FROM information_schema.schemata")
schemas = [s[0] for s in cur.fetchall()]
print(f"SCHEMAS IN CIVIX_DEMO DB: {schemas}")

cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema')")
tables = cur.fetchall()
print("\nALL DATA TABLES:")
for t in tables:
    print(f"  {t[0]}.{t[1]}")

cur.close()
conn.close()

"""Grant necessary permissions to civix_api user for all tables."""
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='postgres', password='postgres'
)
cur = conn.cursor()
print("Connected as postgres superuser")

print("Granting INSERT, UPDATE, DELETE on all tables in civix schema to civix_api")
cur.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA civix TO civix_api")

# Also grant usage on sequences if any
cur.execute("GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA civix TO civix_api")

conn.commit()
cur.close()
conn.close()
print("Done.")

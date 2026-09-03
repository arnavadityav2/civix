import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT trigger_name, action_statement FROM information_schema.triggers WHERE event_object_table='observation'")
print(cur.fetchall())

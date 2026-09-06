import psycopg2

try:
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'location' AND table_schema = 'civix';")
    cols = cur.fetchall()
    print("civix.location columns:")
    for c in cols:
        print(c)
except Exception as e:
    print("Error:", e)

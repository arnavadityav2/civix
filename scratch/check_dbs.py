import psycopg2

for db in ["civix_test", "civix_dev", "civix"]:
    try:
        conn = psycopg2.connect(host='localhost', port=5433, dbname=db, user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx')
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM civix.entity")
        count = cur.fetchone()[0]
        print(f"DB {db}: {count} entities")
        conn.close()
    except Exception as e:
        print(f"DB {db}: failed - {e}")

import psycopg2

def check_gen_origin():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name, column_name 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND column_name LIKE '%generation%';
    """)
    rows = cur.fetchall()
    print("Tables containing 'generation' columns:")
    for t, c in rows:
        print(f"  - Table: civix.{t:<25} | Column: {c}")

    conn.close()

if __name__ == "__main__":
    check_gen_origin()

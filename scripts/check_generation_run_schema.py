import psycopg2

def check_gen_schema():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'generation_run';")
    print("generation_run columns:")
    for col, dt in cur.fetchall():
        print(f"  - {col:<25} : {dt}")
    conn.close()

if __name__ == "__main__":
    check_gen_schema()

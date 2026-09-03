import psycopg2

def inspect_cases():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT case_id, case_number, title FROM civix.investigative_case LIMIT 20;")
    cases = cur.fetchall()
    print("Cases in civix_demo:")
    for cid, cnum, title in cases:
        print(f"  - {cnum:<30} | ID: {cid} | Title: {title}")

    conn.close()

if __name__ == "__main__":
    inspect_cases()

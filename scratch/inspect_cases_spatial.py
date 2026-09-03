import psycopg2

def inspect_cases_spatial():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM civix.investigative_case;")
    tot_cases = cur.fetchone()[0]

    cur.execute("SELECT count(DISTINCT case_id) FROM civix.event_location;")
    cases_with_el = cur.fetchone()[0]

    cur.execute("""
        SELECT c.case_id, c.title, count(el.event_location_id)
        FROM civix.investigative_case c
        JOIN civix.event_location el ON c.case_id = el.case_id
        GROUP BY c.case_id, c.title;
    """)
    cases_el_list = cur.fetchall()

    print(f"Total investigative cases in DB          : {tot_cases}")
    print(f"Cases with event_location records in DB  : {cases_with_el}")
    for c in cases_el_list:
        print(f"  - Case ID: {c[0]} | Title: {c[1]:<35} | Events: {c[2]}")

    conn.close()

if __name__ == "__main__":
    inspect_cases_spatial()

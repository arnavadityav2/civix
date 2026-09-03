import psycopg2
import json

def map_hero_case_uuids():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT case_id, case_number, title FROM civix.investigative_case;")
    db_cases = cur.fetchall()

    print("==========================================================")
    print("MAPPING HERO CASES TO DB UUIDs")
    print("==========================================================")

    # Let's inspect DB case titles and numbers
    hero_map = {}
    for cid, cnum, title in db_cases:
        for i in range(1, 13):
            code = f"HL-00{i}" if i < 10 else f"HL-0{i}"
            full_code = f"DELHI-2026-{code}"
            if code in cnum or code in title or full_code in cnum or full_code in title:
                hero_map[code] = (cid, cnum, title)

    print(f"Matched {len(hero_map)} / 12 hero cases by code.")
    for i in range(1, 13):
        code = f"HL-00{i}" if i < 10 else f"HL-0{i}"
        if code in hero_map:
            cid, cnum, title = hero_map[code]
            print(f"  - {code:<10} => UUID: {cid} | DB Title: {title}")
        else:
            print(f"  - {code:<10} => NOT MATCHED BY CODE. Listing first 5 DB cases...")

    conn.close()

if __name__ == "__main__":
    map_hero_case_uuids()

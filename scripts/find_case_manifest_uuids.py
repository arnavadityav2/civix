import psycopg2
import json

def find_uuids():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("SELECT case_id FROM civix.investigative_case ORDER BY created_at ASC LIMIT 15;")
    db_cids = [r[0] for r in cur.fetchall()]

    with open("demo_world/manifests/investigations.json", "r") as f:
        inv = json.load(f)["investigations"]

    print("==========================================================")
    print("MANIFEST vs DB CASE MATCHING")
    print("==========================================================")
    for i, item in enumerate(inv):
        m_id = item.get("case_id", item.get("id"))
        m_num = item.get("case_number", f"HL-00{i+1}")
        m_title = item.get("title", "")
        print(f"Manifest [{i+1}]: id='{m_id}' | num='{m_num}' | title='{m_title}'")

    print("\nFirst 12 DB case UUIDs:")
    for idx, cid in enumerate(db_cids[:12]):
        cur.execute("SELECT count(*) FROM civix.case_entity_role WHERE case_id = %s;", (cid,))
        roles_cnt = cur.fetchone()[0]
        print(f" DB [{idx+1}]: {cid} (linked entities: {roles_cnt})")

    conn.close()

if __name__ == "__main__":
    find_uuids()

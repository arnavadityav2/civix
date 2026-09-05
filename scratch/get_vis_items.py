import psycopg2, json

DB_CONFIG = {'host': 'localhost', 'port': 5432, 'dbname': 'civix_demo', 'user': 'postgres', 'password': 'postgres'}
conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute("""
    SELECT a.artifact_id, m.manifest_id, m.evidence_id_str, m.evidence_type, m.title, m.case_id
    FROM civix.evidence_artifact a
    JOIN civix.evidence_generation_manifest m ON a.artifact_id = m.artifact_id
    WHERE a.mime_type LIKE 'image/%'
      AND m.evidence_id_str LIKE 'VIS-%'
    ORDER BY m.evidence_id_str;
""")
rows = cur.fetchall()
items = [{'artifact_id': str(r[0]), 'manifest_id': str(r[1]), 'ev_id': r[2], 'ev_type': r[3], 'title': r[4], 'case_id': str(r[5])} for r in rows]
print(f'Total VIS- items: {len(items)}')

from collections import Counter
types = Counter(i['ev_type'] for i in items)
print('Type distribution:', dict(types))

cases = Counter(i['ev_id'].split('-')[1] for i in items)
print('Case num distribution:', dict(cases))

with open('scratch/vis_items.json', 'w') as f:
    json.dump(items, f)
print('Saved scratch/vis_items.json')

cur.execute("SELECT case_id, case_number, title FROM civix.cases ORDER BY case_number;")
case_rows = cur.fetchall()
case_map = {}
for r in case_rows:
    cid, cnum, ctitle = str(r[0]), r[1], r[2]
    case_map[cid] = {'num': cnum, 'title': ctitle}
    print(f'  {cnum}: {ctitle}')

with open('scratch/case_map.json', 'w') as f:
    json.dump(case_map, f)
print('Saved scratch/case_map.json')
conn.close()

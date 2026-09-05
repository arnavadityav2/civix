import psycopg2

def export_prompts():
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()

    cur.execute("""
        SELECT c.case_number, c.title as case_title, m.evidence_id_str, m.evidence_type, m.title as evidence_title, m.prompt, a.artifact_id, a.storage_uri
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
        JOIN civix.evidence_instance ei ON a.artifact_id = ei.artifact_id
        JOIN civix.investigative_case c ON ei.case_id = c.case_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY c.case_number, m.evidence_id_str;
    """)

    rows = cur.fetchall()

    cases = {}
    for r in rows:
        c_num, c_title, ev_id, ev_type, ev_title, prompt, art_id, storage_uri = r
        if c_num not in cases:
            cases[c_num] = {'title': c_title, 'items': []}
        cases[c_num]['items'].append({
            'ev_id': ev_id,
            'ev_type': ev_type,
            'ev_title': ev_title,
            'prompt': prompt,
            'artifact_id': art_id,
            'filename': storage_uri
        })

    md = ['# CIVIX 2.0 — 180 Hero Cases Image Prompts Master Reference\n']
    md.append('This document contains the complete prompt registry for all **180 visual evidence image artifacts** across the **13 Hero Cases**.\n')

    for c_num, data in cases.items():
        md.append(f"## Case: `{c_num}` — {data['title']}")
        md.append(f"**Total Image Artifacts**: {len(data['items'])}\n")
        md.append('| Evidence Ref | Type | Artifact Title | Storage Filename | Generation Prompt |')
        md.append('|---|---|---|---|---|')
        for item in data['items']:
            clean_prompt = item['prompt'].replace('|', '\\|')
            md.append(f"| `{item['ev_id']}` | **{item['ev_type']}** | {item['ev_title']} | `{item['filename']}` | {clean_prompt} |")
        md.append('\n---\n')

    with open('docs/HERO_CASES_IMAGE_PROMPTS.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print('Exported docs/HERO_CASES_IMAGE_PROMPTS.md successfully!')

if __name__ == '__main__':
    export_prompts()

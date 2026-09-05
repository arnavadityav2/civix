import psycopg2
import csv
import json

def export_all():
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()

    cur.execute("""
        SELECT c.case_number, c.title as case_title, m.evidence_id_str, m.evidence_type, m.title as evidence_title, m.prompt, a.storage_uri
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
        JOIN civix.evidence_instance ei ON a.artifact_id = ei.artifact_id
        JOIN civix.investigative_case c ON ei.case_id = c.case_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY c.case_number, m.evidence_id_str;
    """)

    rows = cur.fetchall()

    # 1. CSV File (Excel / Google Sheets)
    with open('docs/HERO_CASES_IMAGE_PROMPTS.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Case Number', 'Case Title', 'Evidence ID', 'Evidence Type', 'Artifact Title', 'Target Filename', 'Prompt'])
        for r in rows:
            writer.writerow(r)

    # 2. TXT File (Clean, unclustered copy-paste format)
    txt_lines = [
        "========================================================================",
        "CIVIX 2.0 — 180 HERO CASE IMAGE PROMPTS MASTER DIRECTORY",
        "========================================================================\n"
    ]

    current_case = None
    for r in rows:
        c_num, c_title, ev_id, ev_type, ev_title, prompt, filename = r
        if c_num != current_case:
            current_case = c_num
            txt_lines.append("\n------------------------------------------------------------------------")
            txt_lines.append(f"CASE: {c_num} — {c_title}")
            txt_lines.append("------------------------------------------------------------------------\n")
        
        txt_lines.append(f"ID:       {ev_id}")
        txt_lines.append(f"TYPE:     {ev_type}")
        txt_lines.append(f"TITLE:    {ev_title}")
        txt_lines.append(f"FILE:     {filename}")
        txt_lines.append(f"PROMPT:   {prompt}")
        txt_lines.append("")

    with open('docs/HERO_CASES_IMAGE_PROMPTS.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(txt_lines))

    # 3. Clean Markdown (Cards/Codeblocks instead of messy wrapped tables)
    md_lines = [
        "# CIVIX 2.0 — 180 Hero Cases Image Prompts Master Reference\n",
        "### 📥 Direct Download Files:\n",
        "- 📊 **[Download CSV File (Opens in Excel / Google Sheets)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.csv)**",
        "- 📝 **[Download Clean Text File (.txt)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.txt)**",
        "- 📦 **[Download JSON File (.json)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.json)**\n",
        "---\n"
    ]

    cases = {}
    for r in rows:
        c_num, c_title, ev_id, ev_type, ev_title, prompt, filename = r
        if c_num not in cases:
            cases[c_num] = {'title': c_title, 'items': []}
        cases[c_num]['items'].append({
            'ev_id': ev_id,
            'ev_type': ev_type,
            'ev_title': ev_title,
            'prompt': prompt,
            'filename': filename
        })

    for c_num, data in cases.items():
        title = data['title']
        md_lines.append(f"## Case `{c_num}` — {title}")
        md_lines.append(f"**Total Images**: {len(data['items'])}\n")
        for item in data['items']:
            ev_id = item['ev_id']
            ev_title = item['ev_title']
            ev_type = item['ev_type']
            filename = item['filename']
            prompt = item['prompt']
            md_lines.append(f"#### `{ev_id}` — {ev_title}")
            md_lines.append(f"- **Type**: `{ev_type}`")
            md_lines.append(f"- **Target Filename**: `{filename}`")
            md_lines.append(f"```text\n{prompt}\n```\n")
        md_lines.append("---\n")

    with open('docs/HERO_CASES_IMAGE_PROMPTS.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print("All downloadable prompt files exported successfully!")

if __name__ == '__main__':
    export_all()

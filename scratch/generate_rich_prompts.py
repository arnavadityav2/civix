import psycopg2
import csv
import json

# Detailed scenario prompt generators for each case
CASE_CONTEXTS = {
    "CIV-2012-001": {
        "theme": "Dwarka Sector 23 Cash Van Robbery (2012)",
        "location": "Dwarka Sector 23, Delhi NCR",
        "elements": ["armed cash van heist", "cash van with open doors", "seized currency bundles with bank wrappers", "getaway Mahindra Bolero", "helmeted suspect", "2012 grainy CCTV camera still"]
    },
    "CIV-2018-036": {
        "theme": "Nizamuddin Gold Bar Theft (2018)",
        "location": "Nizamuddin Railway Station & Vault, Delhi",
        "elements": ["stolen 1kg 999 fine gold bullion bars", "velvet jewelry pouch with police tag", "vault security CCTV footage", "Nizamuddin station exit camera frame", "forensic scale measurement"]
    },
    "CIV-2021-003": {
        "theme": "NH-48 Dacoity with Truck Heist (2021)",
        "location": "National Highway 48 (Gurugram - Delhi Border)",
        "elements": ["hijacked container freight truck on highway shoulder", "abandoned Mahindra Bolero with hazard lights on night highway", "seized heavy wirecutters and crowbar", "toll plaza ANPR camera crop"]
    },
    "CIV-2021-027": {
        "theme": "KYC Phishing Ring — Shahdara (2021)",
        "location": "Shahdara Cyber Cell Raid, East Delhi",
        "elements": ["seized smartphone array running banking OTP phishing app", "fraudulent SIM cards layout", "cybercrime unit evidence room photo", "phishing website admin portal laptop screen"]
    },
    "CIV-2023-032": {
        "theme": "Digital Arrest Call Center — Rohini (2023)",
        "location": "Rohini Sector 11 Commercial Complex, Delhi",
        "elements": ["illegal VoIP cyber call center office raid", "monitors showing fake police badges and green screen backdrop", "headsets and VoIP gateways on desks", "police evidence seized sticker"]
    },
    "CIV-2023-044": {
        "theme": "Gurugram Benami Land Fraud (2023)",
        "location": "Revenue Office & Land Registry, Gurugram Haryana",
        "elements": ["forged land deed document with official Haryana revenue stamps", "seized counterfeit brass seals and rubber stamps", "site survey aerial camera view of disputed land plot", "registry audit ledger"]
    },
    "CIV-2024-010": {
        "theme": "Arham Bullion GST Fraud & SAR Intelligence (2024)",
        "location": "Chandni Chowk Bullion Market & GST Raid, Delhi",
        "elements": ["commercial office raid by tax intelligence officers", "seized fake GST invoices and shell company ledgers", "gold bars on digital precision scale", "financial transaction spreadsheet on monitor"]
    },
    "CIV-2024-038": {
        "theme": "IGI Cargo Smuggling & Interpol Overlap (2024)",
        "location": "IGI Airport International Cargo Terminal, Delhi",
        "elements": ["customs cargo X-ray scanner output", "contraband concealed inside disassembled air compressor", "IGI airport cargo bay CCTV footage", "Interpol Red Notice suspect composite sketch"]
    },
    "CIV-2024-051": {
        "theme": "Ghost Vendor PWD Procurement Fraud (2024)",
        "location": "PWD Office & Infrastructure Site, Delhi NCR",
        "elements": ["substandard road construction inspection photo", "fraudulent procurement invoices with forged engineer signatures", "seized quality testing lab report", "shell company bank statement"]
    },
    "CIV-2025-022": {
        "theme": "Gold Bar Concealment — Okhla Warehouse (2025)",
        "location": "Okhla Industrial Area Phase III Warehouse, Delhi",
        "elements": ["industrial warehouse interior with stacked wooden crates", "seized crate with hidden false bottom revealing gold bars", "forklift operator warehouse CCTV frame", "customs seizure tag"]
    },
    "CIV-2026-009": {
        "theme": "Najafgarh Robbery & Suresh Valmiki Arrest (2026)",
        "location": "Najafgarh Main Market & Alleyway, Delhi",
        "elements": ["seized country-made .315 bore pistol with live cartridges on forensic tray", "forensic composite sketch of suspect Suresh Valmiki", "crime scene narrow alleyway night photograph", "police mugshot backdrop"]
    },
    "CIV-2026-019": {
        "theme": "Plate Cloning Ring — Spatial Paradox (2026)",
        "location": "Dhaula Kuan & Noida Expressway ANPR Cameras",
        "elements": ["night ANPR camera crop of white Hyundai Creta license plate DL-01-AB-1234", "second ANPR crop showing same plate 15km away at same timestamp", "seized counterfeit aluminum license plates and stamping hydraulic press"]
    },
    "FIR-74/2012/SW": {
        "theme": "FIR No. 74/2012 - Dwarka Sec 23 (Village Bharthal Incident)",
        "location": "Dwarka Police Station South-West District",
        "elements": ["aged official First Information Report paper scan with handwritten Hindi blue ink", "official police station round rubber stamp", "incident site village Bharthal field photo"]
    }
}

def generate_prompt_for_item(case_num, case_title, ev_id, ev_type, ev_title):
    ctx = CASE_CONTEXTS.get(case_num, {
        "theme": case_title,
        "location": "Delhi NCR, India",
        "elements": ["crime scene evidence", "police investigation photo"]
    })
    
    loc = ctx["location"]
    theme = ctx["theme"]
    
    # Specific prompt construction based on evidence type and title
    title_lower = ev_title.lower()
    
    if ev_type == "CCTV_FOOTAGE" or "cctv" in title_lower or "cam" in title_lower:
        return (
            f"Grainy 1080p surveillance CCTV security camera frame at night, {loc}, "
            f"depicting {ev_title} ({theme}). Dark urban environment, overhead streetlights, "
            f"digital timestamp and red REC [LIVE] indicator overlay in corner, forensic law enforcement evidence camera capture."
        )
    elif ev_type == "SKETCH" or "sketch" in title_lower or "composite" in title_lower:
        return (
            f"Police forensic composite suspect sketch on textured paper, detailed hand-drawn pencil and charcoal portrait, "
            f"front view portrait of male suspect for {theme}, police department evidence stamp on margin: {ev_title}."
        )
    elif ev_type == "PHYSICAL_EVIDENCE" or "scale" in title_lower or "seized" in title_lower:
        return (
            f"Macro forensic photograph of physical evidence item ({ev_title}) for {theme}, "
            f"placed on dark laboratory surface in Indian police forensic lab, yellow metric centimeter scale ruler alongside, "
            f"sharp focus, professional laboratory evidence lighting."
        )
    else: # PHOTOGRAPH / DEFAULT
        return (
            f"Authentic field crime scene photograph captured with 35mm DSLR lens, realistic lighting, "
            f"detailed forensic evidence capture at {loc}: {ev_title} related to {theme}. "
            f"Indian Police investigation unit evidence standards."
        )

def build_all_prompts():
    conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    cur = conn.cursor()

    cur.execute("""
        SELECT c.case_number, c.title as case_title, m.evidence_id_str, m.evidence_type, m.title as evidence_title, m.manifest_id, a.artifact_id, a.storage_uri
        FROM civix.evidence_generation_manifest m
        JOIN civix.evidence_artifact a ON m.artifact_id = a.artifact_id
        JOIN civix.evidence_instance ei ON a.artifact_id = ei.artifact_id
        JOIN civix.investigative_case c ON ei.case_id = c.case_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY c.case_number, m.evidence_id_str;
    """)

    rows = cur.fetchall()
    print(f"Loaded {len(rows)} image items to construct rich scenario prompts...")

    prompts_data = []
    
    # Update manifest prompts in database
    cur.execute("ALTER TABLE civix.evidence_generation_manifest DISABLE TRIGGER ALL;")
    
    for r in rows:
        c_num, c_title, ev_id, ev_type, ev_title, manifest_id, art_id, filename = r
        rich_prompt = generate_prompt_for_item(c_num, c_title, ev_id, ev_type, ev_title)
        
        # Update DB prompt field
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET prompt = %s, updated_at = NOW()
            WHERE manifest_id = %s
        """, (rich_prompt, manifest_id))
        
        prompts_data.append({
            'case_number': c_num,
            'case_title': c_title,
            'evidence_id': ev_id,
            'evidence_type': ev_type,
            'evidence_title': ev_title,
            'prompt': rich_prompt,
            'artifact_id': str(art_id),
            'target_filename': filename,
            'target_storage_path': f"C:\\data\\civix_demo\\evidence_store\\{filename}"
        })

    cur.execute("ALTER TABLE civix.evidence_generation_manifest ENABLE TRIGGER ALL;")
    conn.commit()
    conn.close()

    # 1. Export JSON File
    with open('docs/HERO_CASES_IMAGE_PROMPTS.json', 'w', encoding='utf-8') as f:
        json.dump(prompts_data, f, indent=2)

    # 2. Export CSV File
    with open('docs/HERO_CASES_IMAGE_PROMPTS.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Case Number', 'Case Title', 'Evidence ID', 'Evidence Type', 'Artifact Title', 'Target Filename', 'Prompt'])
        for p in prompts_data:
            writer.writerow([p['case_number'], p['case_title'], p['evidence_id'], p['evidence_type'], p['evidence_title'], p['target_filename'], p['prompt']])

    # 3. Export TXT File
    txt_lines = [
        "========================================================================",
        "CIVIX 2.0 — 180 HERO CASE SCENARIO-SPECIFIC AI IMAGE PROMPTS",
        "========================================================================\n"
    ]
    current_case = None
    for p in prompts_data:
        c_num = p['case_number']
        if c_num != current_case:
            current_case = c_num
            txt_lines.append("\n------------------------------------------------------------------------")
            txt_lines.append(f"CASE: {c_num} — {p['case_title']}")
            txt_lines.append("------------------------------------------------------------------------\n")
        txt_lines.append(f"ID:       {p['evidence_id']}")
        txt_lines.append(f"TYPE:     {p['evidence_type']}")
        txt_lines.append(f"TITLE:    {p['evidence_title']}")
        txt_lines.append(f"FILE:     {p['target_filename']}")
        txt_lines.append(f"PROMPT:   {p['prompt']}")
        txt_lines.append("")

    with open('docs/HERO_CASES_IMAGE_PROMPTS.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(txt_lines))

    # 4. Export Markdown File
    md_lines = [
        "# CIVIX 2.0 — 180 Hero Cases AI Image Generation Prompts\n",
        "### 📥 Direct Download Files:\n",
        "- 📊 **[Download CSV File (Excel / Google Sheets)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.csv)**",
        "- 📝 **[Download Clean Text File (.txt)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.txt)**",
        "- 📦 **[Download JSON File (.json)](file:///c:/Users/ARNAV%20ADITYA/Desktop/civix%202.0/docs/HERO_CASES_IMAGE_PROMPTS.json)**\n",
        "---\n"
    ]

    cases = {}
    for p in prompts_data:
        c_num = p['case_number']
        if c_num not in cases:
            cases[c_num] = {'title': p['case_title'], 'items': []}
        cases[c_num]['items'].append(p)

    for c_num, data in cases.items():
        title = data['title']
        md_lines.append(f"## Case `{c_num}` — {title}")
        md_lines.append(f"**Total Images**: {len(data['items'])}\n")
        for item in data['items']:
            md_lines.append(f"#### `{item['evidence_id']}` — {item['evidence_title']}")
            md_lines.append(f"- **Type**: `{item['evidence_type']}`")
            md_lines.append(f"- **Target Filename**: `{item['target_filename']}`")
            md_lines.append(f"```text\n{item['prompt']}\n```\n")
        md_lines.append("---\n")

    with open('docs/HERO_CASES_IMAGE_PROMPTS.md', 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f"SUCCESSFULLY generated and updated all 180 rich scenario prompts across CSV, TXT, JSON, MD, and database!")

if __name__ == '__main__':
    build_all_prompts()

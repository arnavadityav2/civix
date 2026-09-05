import os
import psycopg2
import json

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

ARTIFACTS_DIR = r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\7ed066df-c376-49fb-9bf5-41c309f40bd2"

def analyze():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
        SELECT evidence_id_str, evidence_type, title, prompt 
        FROM civix.evidence_generation_manifest 
        WHERE expected_mime_type = 'image/png'
    """)
    rows = cur.fetchall()
    
    generic_keywords = ['warehouse', 'toll plaza', 'hospital', 'currency notes', 'passport', 'visa', 'cash', 'pistol', 'office building', 'generic', 'street']
    
    tier1_generic = []
    tier2_specific = []
    tier3_cctv = []
    
    for row in rows:
        ev_id, ev_type, title, prompt = row
        prompt_lower = prompt.lower()
        title_lower = title.lower()
        
        if ev_type == 'CCTV_FOOTAGE':
            tier3_cctv.append(row)
        elif ev_type == 'SKETCH':
            tier2_specific.append(row) # Sketches are hard to source randomly
        else:
            # Check for generic keywords
            is_generic = False
            for k in generic_keywords:
                if k in prompt_lower or k in title_lower:
                    is_generic = True
                    break
            
            if is_generic:
                tier1_generic.append(row)
            else:
                tier2_specific.append(row)
                
    md_content = f"""# CIVIX 2.0 — Visual Evidence Sourcing Strategy

Based on your suggestion, I have categorized the 180 visual artifacts to minimize Gemini generations and maximize open-internet sourcing.

## TIER 1: Generic Items (Can be sourced from the Internet) — {len(tier1_generic)} Items
These items represent generic objects, locations, or physical items that can easily be found via open web searches (e.g., standard stock photos of cash, generic office buildings, generic handguns, warehouses).

**Examples from this category:**
"""
    for r in tier1_generic[:10]:
        md_content += f"- **{r[0]}** ({r[1]}): {r[2]}\n"
    if len(tier1_generic) > 10:
        md_content += f"- *...and {len(tier1_generic) - 10} more generic items.*\n"

    md_content += f"""
## TIER 2: Highly Specific Items (Must use Gemini) — {len(tier2_specific)} Items
These items represent highly specific forensic combinations that are virtually impossible to find randomly on the internet (e.g., specific composite suspect sketches, gold bars hidden *inside* a car door, highly specific cybercrime raid desks with multiple burner phones).

**Examples from this category:**
"""
    for r in tier2_specific[:10]:
        md_content += f"- **{r[0]}** ({r[1]}): {r[2]}\n"
    if len(tier2_specific) > 10:
        md_content += f"- *...and {len(tier2_specific) - 10} more highly specific items.*\n"

    md_content += f"""
## TIER 3: CCTV & Surveillance (Hybrid Approach) — {len(tier3_cctv)} Items
These must have exact timestamps and database-accurate text (like License Plates) stamped on them. We can use internet photos for the background, but we still must use a Python script to stamp the correct text onto them so they don't break the database logic.

**Examples from this category:**
"""
    for r in tier3_cctv[:5]:
        md_content += f"- **{r[0]}** ({r[1]}): {r[2]}\n"
    if len(tier3_cctv) > 5:
        md_content += f"- *...and {len(tier3_cctv) - 5} more CCTV items.*\n"

    md_content += """
---
### Proposed Workflow
1. **You** (or a script) find and download the internet images for **Tier 1** and **Tier 3 (backgrounds)** and drop them into a folder.
2. **I** will use Gemini to exclusively generate the highly specific **Tier 2** images.
3. **I** will write a script to take your internet images, my Gemini images, stamp the text onto the CCTV ones, and safely map everything into the `civix_demo` database and `evidence_store`.
"""

    with open(os.path.join(ARTIFACTS_DIR, "VISUAL_SOURCE_STRATEGY.md"), "w", encoding="utf-8") as f:
        f.write(md_content)
        
    print(f"Tier 1 (Internet): {len(tier1_generic)}")
    print(f"Tier 2 (Gemini): {len(tier2_specific)}")
    print(f"Tier 3 (CCTV): {len(tier3_cctv)}")

if __name__ == "__main__":
    analyze()

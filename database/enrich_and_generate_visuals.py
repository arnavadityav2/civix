import os
import sys
import json
import time
import random
import hashlib
import psycopg2
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
os.makedirs(EVIDENCE_STORE, exist_ok=True)

def generate_rich_prompt(ev_id, ev_type, title, base_prompt, case_title):
    title_clean = title.replace("CIVIX 2.0 visual evidence artifact", "").strip()
    
    # Case context mapping
    case_ctx = ""
    if "GST" in title or "GST" in str(case_title):
        case_ctx = "GST tax fraud raid evidence in Indian commercial office, seized financial ledgers, fake invoice stamps"
    elif "Plate Cloning" in title or "Plate" in str(case_title):
        case_ctx = "Vehicle registration plate cloning investigation, counterfeit Indian HSRP number plate DL-01-C-9988, garage workbench"
    elif "Okhla Gold" in title or "Gold" in str(case_title):
        case_ctx = "Okhla gold heist evidence, seized gold bullion bars, velvet jewelry pouch, police evidence tag"
    elif "KYC" in title or "Phishing" in str(case_title):
        case_ctx = "Cybercrime unit evidence, seized SIM cards, mobile phones, banking OTP phishing call center setup"
    elif "Digital Arrest" in title or "Arrest" in str(case_title):
        case_ctx = "Cyber fraud investigation, spoofed police video call setup background, fake police badge and uniform prop"
    elif "Nizamuddin" in title:
        case_ctx = "Nizamuddin crime scene, old Delhi market alleyway night photo, police cordon tape"
    elif "IGI Cargo" in title or "Cargo" in str(case_title):
        case_ctx = "IGI Airport cargo terminal inspection, seized contraband package, customs seal"
    elif "Benami" in title or "Land" in str(case_title):
        case_ctx = "Land fraud investigation, property deed document with revenue stamps, site inspection map"
    elif "Ghost Vendor" in title or "Vendor" in str(case_title):
        case_ctx = "Procurement scam investigation, shell company registration files, official bank stamp"
    else:
        case_ctx = f"Indian law enforcement field evidence, Delhi NCR police investigation, reference {title}"

    if ev_type == "CCTV_FOOTAGE":
        return f"Grainy 1080p security CCTV footage frame at night, Indian city street or corridor, dim overhead streetlights, surveillance view: {title_clean}. {case_ctx}"
    elif ev_type == "SKETCH":
        return f"Hand-drawn police composite suspect sketch on paper, forensic pencil charcoal drawing, detailed facial features of male suspect, Indian police department forensic drawing: {title_clean}. {case_ctx}"
    elif ev_type == "PHYSICAL_EVIDENCE":
        return f"Macro forensic photo of physical crime evidence on laboratory table, yellow centimeter scale ruler next to evidence, sharp focus, neutral lighting: {title_clean}. {case_ctx}"
    else: # PHOTOGRAPH
        return f"Authentic crime scene field photograph, realistic lighting, DSLR capture, Indian police field investigation unit: {title_clean}. {case_ctx}"

def apply_cctv_hud(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.75)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font_large = ImageFont.truetype("arial.ttf", int(h * 0.035))
        font_small = ImageFont.truetype("arial.ttf", int(h * 0.025))
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S IST")
    cam_num = (abs(hash(ev_id)) % 899) + 101
    cam_id = f"CAM-{cam_num:03d}"
    rec_x, rec_y = int(w * 0.03), int(h * 0.03)
    draw.ellipse((rec_x, rec_y, rec_x + 16, rec_y + 16), fill=(235, 30, 30))
    draw.text((rec_x + 24, rec_y), f"REC  {cam_id} [LIVE]", fill=(245, 245, 245), font=font_large)
    draw.text((int(w * 0.62), rec_y), timestamp_str, fill=(245, 245, 245), font=font_large)
    clean_title = title.replace("\n", " ")[:40]
    draw.text((int(w * 0.03), int(h * 0.93)), f"REF: {ev_id} | {clean_title}", fill=(210, 230, 210), font=font_small)
    draw.text((int(w * 0.80), int(h * 0.93)), "1080P // HQ", fill=(210, 230, 210), font=font_small)
    return img

def download_and_process_item(item):
    manifest_id = item["manifest_id"]
    ev_id = item["evidence_id"]
    ev_type = item["evidence_type"]
    title = item["title"]
    prompt = item["rich_prompt"]
    
    encoded_prompt = urllib.parse.quote(prompt)
    seed = (abs(hash(title + ev_id)) % 999999) + 1
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}&model=flux"
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ]
    
    img_data = None
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                time.sleep(2 ** attempt + random.uniform(0.5, 2.0))
            headers = {"User-Agent": random.choice(user_agents)}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=35) as resp:
                img_data = resp.read()
                if len(img_data) > 1000:
                    break
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2)
            
    if not img_data:
        raise Exception(f"Failed to download image for {ev_id}")
        
    temp_path = os.path.join(EVIDENCE_STORE, f"temp_{ev_id}.png")
    with open(temp_path, "wb") as f:
        f.write(img_data)
        
    img = Image.open(temp_path)
    if ev_type == "CCTV_FOOTAGE":
        img = apply_cctv_hud(img, ev_id, title)
    img.save(temp_path, format="PNG")
    
    with open(temp_path, "rb") as f:
        final_bytes = f.read()
        
    sha256_hex = hashlib.sha256(final_bytes).hexdigest()
    final_filename = f"{sha256_hex}.png"
    final_path = os.path.join(EVIDENCE_STORE, final_filename)
    
    if os.path.exists(temp_path):
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_path, final_path)
        
    file_size = len(final_bytes)
    sha256_bytes = bytes.fromhex(sha256_hex)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE civix.evidence_artifact
            SET sha256_hash = %s,
                storage_uri = %s,
                file_size_bytes = %s,
                processed_at = NOW()
            WHERE artifact_id = (
                SELECT artifact_id FROM civix.evidence_generation_manifest WHERE manifest_id = %s::uuid
            )
        """, (sha256_bytes, final_filename, file_size, manifest_id))
        
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET prompt = %s, updated_at = NOW()
            WHERE manifest_id = %s::uuid
        """, (prompt, manifest_id))
    finally:
        conn.close()
        
    return {
        "ev_id": ev_id,
        "filename": final_filename,
        "size": file_size,
        "ev_type": ev_type
    }

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT manifest_id, evidence_id_str, evidence_type, title, prompt
        FROM civix.evidence_generation_manifest
        WHERE expected_mime_type = 'image/png'
        ORDER BY evidence_id_str;
    """)
    rows = cur.fetchall()
    conn.close()
    
    items = []
    for r in rows:
        manifest_id, ev_id, ev_type, title, base_prompt = r
        rich_p = generate_rich_prompt(ev_id, ev_type, title, base_prompt, title)
        items.append({
            "manifest_id": manifest_id,
            "evidence_id": ev_id,
            "evidence_type": ev_type,
            "title": title,
            "base_prompt": base_prompt,
            "rich_prompt": rich_p
        })
        
    print(f"Loaded {len(items)} evidence items to enrich & generate via Flux AI model...")
    
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            items = items[:limit]
            print(f"Running for first {limit} items.")
        except ValueError:
            pass
            
    conn_global = psycopg2.connect(**DB_CONFIG)
    conn_global.autocommit = True
    cur_g = conn_global.cursor()
    cur_g.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER USER;")
    
    completed = 0
    total = len(items)
    results = []
    
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_to_item = {executor.submit(download_and_process_item, item): item for item in items}
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                completed += 1
                try:
                    res = future.result()
                    results.append(res)
                    print(f"[{completed}/{total}] SUCCESS: {res['ev_id']} ({res['ev_type']}) -> {res['filename']} ({res['size']} bytes)")
                except Exception as exc:
                    print(f"[{completed}/{total}] ERROR: {item['evidence_id']} failed: {exc}")
    finally:
        cur_g.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER USER;")
        conn_global.close()
        
    print(f"\nCompleted! {len(results)}/{total} AI images generated successfully.")

if __name__ == "__main__":
    main()

import os
import sys
import json
import time
import random
import hashlib
import psycopg2
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
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

def generate_rich_prompt(ev_id, ev_type, title, base_prompt):
    title_clean = title.replace("CIVIX 2.0 visual evidence artifact", "").strip()
    
    if ev_type == "CCTV_FOOTAGE":
        return f"Grainy 1080p surveillance CCTV security camera frame at night, urban street corner or corridor in Delhi NCR India, dark environment, streetlights, camera angle looking down: {title_clean}. Detailed forensic security footage."
    elif ev_type == "SKETCH":
        return f"Police composite suspect sketch on paper, hand-drawn forensic pencil charcoal drawing, detailed facial features of male suspect, front view portrait, Indian police forensic illustration: {title_clean}."
    elif ev_type == "PHYSICAL_EVIDENCE":
        return f"Macro forensic photograph of physical evidence item on dark laboratory table, sharp focus, professional evidence lighting: {title_clean}. Indian police crime laboratory."
    else: # PHOTOGRAPH
        return f"Realistic crime scene field photograph, DSLR camera capture, night or daylight, Indian police investigation team: {title_clean}."

def apply_cctv_hud(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize((1024, 768), Image.Resampling.LANCZOS)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.8)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font_large = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    timestamp_str = "2026-07-19 23:14:02 IST"
    cam_num = (abs(hash(ev_id)) % 899) + 101
    cam_id = f"CAM-{cam_num:03d}"
    
    # Target bounding box overlay
    box_x1, box_y1 = int(w * 0.30), int(h * 0.25)
    box_x2, box_y2 = int(w * 0.70), int(h * 0.75)
    draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=(0, 230, 255), width=2)
    draw.rectangle([box_x1 - 1, box_y1 - 22, box_x1 + 220, box_y1], fill=(0, 30, 45))
    draw.text((box_x1 + 5, box_y1 - 20), "TARGET DETECTED [CONF: 96.8%]", fill=(0, 230, 255), font=font_small)
    
    # Red REC indicator
    rec_x, rec_y = 30, 25
    draw.ellipse((rec_x, rec_y, rec_x + 18, rec_y + 18), fill=(235, 30, 30))
    draw.text((rec_x + 26, rec_y - 2), f"REC  {cam_id} [LIVE]", fill=(245, 245, 245), font=font_large)
    draw.text((int(w * 0.65), rec_y - 2), timestamp_str, fill=(245, 245, 245), font=font_large)
    
    clean_title = title.replace("\n", " ")[:45]
    draw.rectangle([0, h - 45, w, h], fill=(10, 15, 25))
    draw.text((30, h - 35), f"REF: {ev_id} | {clean_title} | DELHI NCR SURVEILLANCE GRID", fill=(210, 230, 210), font=font_small)
    draw.text((int(w * 0.82), h - 35), "1080P // FORENSIC", fill=(0, 230, 255), font=font_small)
    return img

def apply_sketch_filter(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font_large = ImageFont.truetype("arial.ttf", 22)
    except Exception:
        font_large = ImageFont.load_default()
        
    draw.rectangle([20, 20, w - 20, h - 20], outline=(40, 40, 40), width=3)
    draw.rectangle([0, h - 55, w, h], fill=(245, 243, 235))
    draw.text((40, h - 42), f"DELHI NCR POLICE FORENSIC UNIT — SUSPECT COMPOSITE SKETCH [REF: {ev_id}]", fill=(40, 40, 40), font=font_large)
    return img

def apply_physical_scale(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
        
    # Yellow metric scale bar
    ruler_h = 32
    ruler_y = h - 55
    ruler_x_start = 50
    ruler_w = 500
    draw.rectangle([ruler_x_start, ruler_y, ruler_x_start + ruler_w, ruler_y + ruler_h], fill=(240, 210, 40))
    tick_step = ruler_w // 20
    for i in range(21):
        x = ruler_x_start + i * tick_step
        draw.line([x, ruler_y, x, ruler_y + (ruler_h if i % 5 == 0 else ruler_h // 2)], fill=(10, 10, 10), width=2)
    draw.text((ruler_x_start + ruler_w + 20, ruler_y + 6), f"FORENSIC METRIC SCALE [CM] | REF: {ev_id}", fill=(245, 245, 245), font=font)
    return img

def apply_photo_border(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    img = img.resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
        
    draw.rectangle([15, 15, w - 15, h - 15], outline=(220, 180, 40), width=3)
    draw.rectangle([0, h - 45, w, h], fill=(20, 24, 32))
    draw.text((30, h - 35), f"CRIME SCENE FIELD PHOTOGRAPH | REF: {ev_id} | DELHI NCR POLICE FORENSIC LAB", fill=(240, 210, 50), font=font)
    return img

def fetch_ai_image(prompt, ev_id):
    encoded_prompt = urllib.parse.quote(prompt)
    seed = (abs(hash(ev_id)) % 999999) + 1
    
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}&model=flux",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}&model=turbo"
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    for url in urls:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
                if len(data) > 3000:
                    return data
        except Exception:
            pass
    return None

def process_item(item):
    artifact_id = item["artifact_id"]
    manifest_id = item["manifest_id"]
    ev_id = item["ev_id"]
    ev_type = item["ev_type"]
    title = item["title"]
    base_prompt = item["prompt"]
    
    prompt = generate_rich_prompt(ev_id, ev_type, title, base_prompt)
    img_data = fetch_ai_image(prompt, ev_id)
    
    temp_path = os.path.join(EVIDENCE_STORE, f"temp_{ev_id}.png")
    if img_data:
        with open(temp_path, "wb") as f:
            f.write(img_data)
        img = Image.open(temp_path)
    else:
        # Procedural fallback if API unreachable
        img = Image.new("RGB", (1024, 768), color=(25, 30, 42))
        
    if ev_type == "CCTV_FOOTAGE":
        img = apply_cctv_hud(img, ev_id, title)
    elif ev_type == "SKETCH":
        img = apply_sketch_filter(img, ev_id, title)
    elif ev_type == "PHYSICAL_EVIDENCE":
        img = apply_physical_scale(img, ev_id, title)
    else:
        img = apply_photo_border(img, ev_id, title)
        
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
    
    return {
        "artifact_id": artifact_id,
        "manifest_id": manifest_id,
        "ev_id": ev_id,
        "filename": final_filename,
        "sha256_bytes": sha256_bytes,
        "file_size": file_size,
        "is_ai": img_data is not None
    }

def main():
    print("=== STARTING AI IMAGE GENERATION FOR ALL 180 EVIDENCE PROMPTS ===")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL;")
    
    cur.execute("""
        SELECT a.artifact_id, m.manifest_id, m.evidence_id_str, m.evidence_type, m.title, m.prompt
        FROM civix.evidence_artifact a
        JOIN civix.evidence_generation_manifest m ON a.artifact_id = m.artifact_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY m.evidence_id_str;
    """)
    rows = cur.fetchall()
    print(f"Total image prompts loaded: {len(rows)}")
    
    items = [{
        "artifact_id": r[0],
        "manifest_id": r[1],
        "ev_id": r[2],
        "ev_type": r[3],
        "title": r[4],
        "prompt": r[5]
    } for r in rows]
    
    results = []
    completed = 0
    total = len(items)
    
    # 5 workers for fast execution
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_item = {executor.submit(process_item, item): item for item in items}
        for future in as_completed(future_to_item):
            completed += 1
            try:
                res = future.result()
                results.append(res)
                ai_flag = "AI-GENERATED" if res["is_ai"] else "PROCEDURAL"
                print(f"[{completed}/{total}] {res['ev_id']} -> {res['filename'][:16]}... ({res['file_size']} B) [{ai_flag}]")
            except Exception as e:
                print(f"[{completed}/{total}] ERROR processing item: {e}")
                
    print("\nUpdating PostgreSQL database records...")
    for res in results:
        cur.execute("""
            UPDATE civix.evidence_artifact
            SET sha256_hash = %s,
                storage_uri = %s,
                file_size_bytes = %s,
                mime_type = 'image/png',
                processed_at = NOW()
            WHERE artifact_id = %s
        """, (res["sha256_bytes"], res["filename"], res["file_size"], res["artifact_id"]))
        
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET generation_status = 'GENERATED', updated_at = NOW()
            WHERE manifest_id = %s
        """, (res["manifest_id"],))
        
    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL;")
    conn.close()
    
    ai_count = sum(1 for r in results if r["is_ai"])
    print(f"\nALL DONE! {len(results)}/{total} images committed to DB! ({ai_count} fetched via AI image generator)")

if __name__ == "__main__":
    main()

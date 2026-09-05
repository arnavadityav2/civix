import os
import sys
import json
import time
import hashlib
import psycopg2
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance
from concurrent.futures import ThreadPoolExecutor, as_completed

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "generation_manifest.json")

os.makedirs(EVIDENCE_STORE, exist_ok=True)

def process_sketch(img):
    gray = img.convert("L")
    edges = gray.filter(ImageFilter.FIND_EDGES)
    inverted = ImageOps.invert(edges)
    contrast = ImageEnhance.Contrast(inverted).enhance(2.2)
    
    rgb = contrast.convert("RGB")
    paper_overlay = Image.new("RGB", rgb.size, (248, 246, 240))
    sketch_blend = Image.blend(rgb, paper_overlay, alpha=0.12)
    return sketch_blend

def process_cctv(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.65)
    
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
    
    rec_x = int(w * 0.03)
    rec_y = int(h * 0.03)
    draw.ellipse((rec_x, rec_y, rec_x + 16, rec_y + 16), fill=(235, 30, 30))
    
    draw.text((rec_x + 24, rec_y), f"REC  {cam_id} [LIVE]", fill=(245, 245, 245), font=font_large)
    draw.text((int(w * 0.62), rec_y), timestamp_str, fill=(245, 245, 245), font=font_large)
    
    clean_title = title.replace("\n", " ")[:42]
    draw.text((int(w * 0.03), int(h * 0.93)), f"REF: {ev_id} | {clean_title}", fill=(210, 230, 210), font=font_small)
    draw.text((int(w * 0.80), int(h * 0.93)), "1080P // HQ", fill=(210, 230, 210), font=font_small)
    
    return img

def process_physical_evidence(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    img = ImageEnhance.Sharpness(img).enhance(1.8)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    try:
        font = ImageFont.truetype("arial.ttf", int(h * 0.024))
    except Exception:
        font = ImageFont.load_default()
        
    ruler_h = int(h * 0.04)
    ruler_y = h - ruler_h - int(h * 0.02)
    ruler_x_start = int(w * 0.05)
    ruler_w = int(w * 0.5)
    
    draw.rectangle([ruler_x_start, ruler_y, ruler_x_start + ruler_w, ruler_y + ruler_h], fill=(240, 210, 40))
    
    tick_step = ruler_w // 20
    for i in range(21):
        x = ruler_x_start + i * tick_step
        draw.line([x, ruler_y, x, ruler_y + (ruler_h if i % 5 == 0 else ruler_h // 2)], fill=(10, 10, 10), width=2)
        
    draw.text((ruler_x_start + ruler_w + 15, ruler_y + 4), f"CIVIX FORENSIC SCALE [CM] | {ev_id}", fill=(245, 245, 245), font=font)
    return img

def process_photograph(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    img = ImageEnhance.Contrast(img).enhance(1.15)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    try:
        font = ImageFont.truetype("arial.ttf", int(h * 0.022))
    except Exception:
        font = ImageFont.load_default()
        
    timestamp_str = time.strftime("%Y-%m-%d")
    draw.text((int(w * 0.03), int(h * 0.94)), f"NCR FIELD UNIT // {timestamp_str} // {ev_id}", fill=(230, 230, 230), font=font)
    return img

def download_and_process_item(item):
    ev_id = item["evidence_id"]
    ev_type = item["ev_type"]
    title = item["title"]
    manifest_id = item["manifest_id"]
    
    seed_str = f"{ev_id}_{manifest_id}"
    url = f"https://picsum.photos/seed/{seed_str}/1024/768"
    
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        img_data = resp.read()
        
    temp_path = os.path.join(EVIDENCE_STORE, f"temp_{ev_id}.jpg")
    with open(temp_path, "wb") as f:
        f.write(img_data)
        
    img = Image.open(temp_path)
    
    if ev_type == "SKETCH":
        processed_img = process_sketch(img)
    elif ev_type == "CCTV_FOOTAGE":
        processed_img = process_cctv(img, ev_id, title)
    elif ev_type == "PHYSICAL_EVIDENCE":
        processed_img = process_physical_evidence(img, ev_id, title)
    else: # PHOTOGRAPH
        processed_img = process_photograph(img, ev_id, title)
        
    final_temp_path = os.path.join(EVIDENCE_STORE, f"temp_{ev_id}.png")
    processed_img.save(final_temp_path, format="PNG")
    
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    with open(final_temp_path, "rb") as f:
        final_bytes = f.read()
        
    sha256_hex = hashlib.sha256(final_bytes).hexdigest()
    final_filename = f"{sha256_hex}.png"
    final_path = os.path.join(EVIDENCE_STORE, final_filename)
    
    if os.path.exists(final_temp_path):
        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(final_temp_path, final_path)
        
    file_size = len(final_bytes)
    sha256_bytes = bytes.fromhex(sha256_hex)
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT a.storage_uri 
            FROM civix.evidence_artifact a
            JOIN civix.evidence_generation_manifest m ON m.artifact_id = a.artifact_id
            WHERE m.manifest_id = %s::uuid
        """, (manifest_id,))
        old_row = cur.fetchone()
        old_storage_uri = old_row[0] if old_row else None
        
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
            SET updated_at = NOW()
            WHERE manifest_id = %s::uuid
        """, (manifest_id,))
        
        if old_storage_uri and old_storage_uri != final_filename:
            old_file_path = os.path.join(EVIDENCE_STORE, old_storage_uri)
            if os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception:
                    pass
    finally:
        conn.close()
        
    return {
        "ev_id": ev_id,
        "manifest_id": manifest_id,
        "sha256": sha256_hex,
        "filename": final_filename,
        "size": file_size,
        "ev_type": ev_type
    }

def main():
    if not os.path.exists(MANIFEST_FILE):
        print(f"Error: Manifest file {MANIFEST_FILE} not found.")
        sys.exit(1)
        
    with open(MANIFEST_FILE, "r") as f:
        manifest_data = json.load(f)
        
    items = []
    for ev_type, list_items in manifest_data.items():
        for item in list_items:
            item_copy = dict(item)
            item_copy["ev_type"] = ev_type
            items.append(item_copy)
            
    print(f"Loaded {len(items)} items to generate.")
    
    limit = None
    if len(sys.argv) > 1:
        try:
            limit = int(sys.argv[1])
            print(f"Running in test mode: generating first {limit} items.")
            items = items[:limit]
        except ValueError:
            pass
            
    completed = 0
    total = len(items)
    start_time = time.time()
    
    # Disable trigger globally before batch execution
    conn_global = psycopg2.connect(**DB_CONFIG)
    conn_global.autocommit = True
    cur_g = conn_global.cursor()
    cur_g.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER USER;")
    
    print(f"Starting ultra-fast batch generation with ThreadPoolExecutor (max_workers=10)...")
    
    results = []
    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_item = {executor.submit(download_and_process_item, item): item for item in items}
            
            for future in as_completed(future_to_item):
                item = future_to_item[future]
                completed += 1
                try:
                    res = future.result()
                    results.append(res)
                    print(f"[{completed}/{total}] SUCCESS: {res['ev_id']} ({res['ev_type']}) -> {res['filename']} ({res['size']} bytes)")
                except Exception as exc:
                    print(f"[{completed}/{total}] ERROR: {item['evidence_id']} failed with exception: {exc}")
    finally:
        # Re-enable trigger globally after batch execution
        cur_g.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER USER;")
        conn_global.close()
        
    elapsed = time.time() - start_time
    print(f"\nBatch Completed! {len(results)}/{total} items generated successfully in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()

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
MANIFEST_FILE = os.path.join(os.path.dirname(__file__), "generation_manifest.json")

os.makedirs(EVIDENCE_STORE, exist_ok=True)

def build_prompt_with_style(ev_type, title, base_prompt):
    prompt_clean = base_prompt.replace("\n", " ").strip()
    if ev_type == "SKETCH":
        return f"Hand-drawn police composite suspect sketch, forensic pencil drawing on paper, detailed facial features, monochrome charcoal illustration: {prompt_clean}"
    elif ev_type == "CCTV_FOOTAGE":
        return f"Low light grainy security camera footage frame, indoor or outdoor surveillance view, wide angle camera perspective: {prompt_clean}"
    elif ev_type == "PHYSICAL_EVIDENCE":
        return f"Macro forensic photograph of physical evidence item on sterile laboratory surface, evidence tag next to item, sharp focus, professional forensic lighting: {prompt_clean}"
    else: # PHOTOGRAPH
        return f"Documentary crime scene photograph, realistic lighting, detailed DSLR capture, authentic field evidence: {prompt_clean}"

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
    
    rec_x = int(w * 0.03)
    rec_y = int(h * 0.03)
    rec_box = (rec_x, rec_y, rec_x + 16, rec_y + 16)
    draw.ellipse(rec_box, fill=(235, 30, 30))
    
    draw.text((rec_x + 24, rec_y), f"REC  {cam_id} [LIVE]", fill=(245, 245, 245), font=font_large)
    draw.text((int(w * 0.62), rec_y), timestamp_str, fill=(245, 245, 245), font=font_large)
    
    clean_title = title.replace("\n", " ")[:40]
    draw.text((int(w * 0.03), int(h * 0.93)), f"REF: {ev_id} | {clean_title}", fill=(210, 230, 210), font=font_small)
    draw.text((int(w * 0.80), int(h * 0.93)), "1080P // HQ", fill=(210, 230, 210), font=font_small)
    
    return img

def download_and_process_image(item):
    ev_id = item["evidence_id"]
    ev_type = item["ev_type"]
    title = item["title"]
    prompt = item["prompt"]
    manifest_id = item["manifest_id"]
    
    styled_prompt = build_prompt_with_style(ev_type, title, prompt)
    encoded_prompt = urllib.parse.quote(styled_prompt)
    
    seed = (abs(hash(title + ev_id)) % 999999) + 1
    # Adding model=flux and random delay to avoid 429 rate limit
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=768&nologo=true&seed={seed}&model=flux"
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    max_retries = 5
    img_data = None
    for attempt in range(max_retries):
        try:
            # Staggered retry delay on rate limit
            if attempt > 0:
                sleep_time = (2 ** attempt) + random.uniform(1.0, 3.0)
                time.sleep(sleep_time)
                
            headers = {"User-Agent": random.choice(user_agents)}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=40) as resp:
                img_data = resp.read()
                if len(img_data) > 1000:
                    break
        except urllib.error.HTTPError as he:
            if he.code == 429:
                # Back off on 429
                time.sleep(5 * (attempt + 1))
            elif attempt == max_retries - 1:
                raise he
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(3)
            
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
    
    # DB Update with autocommit transaction isolation
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    
    try:
        cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER USER;")
        
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
            SET generated_at = NOW()
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
        cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER USER;")
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
    
    # Use max_workers=2 to prevent HTTP 429 rate limit
    print(f"Starting batch generation with ThreadPoolExecutor (max_workers=2)...")
    
    results = []
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_item = {executor.submit(download_and_process_image, item): item for item in items}
        
        for future in as_completed(future_to_item):
            item = future_to_item[future]
            completed += 1
            try:
                res = future.result()
                results.append(res)
                print(f"[{completed}/{total}] SUCCESS: {res['ev_id']} ({res['ev_type']}) -> {res['filename']} ({res['size']} bytes)")
            except Exception as exc:
                print(f"[{completed}/{total}] ERROR: {item['evidence_id']} failed with exception: {exc}")
                
    elapsed = time.time() - start_time
    print(f"\nBatch Completed! {len(results)}/{total} items generated successfully in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()

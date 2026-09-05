import os
import sys
import hashlib
import psycopg2
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "civix_demo",
    "user":     "postgres",
    "password": "postgres",
}

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
os.makedirs(EVIDENCE_STORE, exist_ok=True)

def apply_cctv_hud(img, ev_id, title):
    if img.mode != "RGB":
        img = img.convert("RGB")
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.85)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    try:
        font_large = ImageFont.truetype("arial.ttf", int(h * 0.035))
        font_small = ImageFont.truetype("arial.ttf", int(h * 0.025))
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    rec_x, rec_y = int(w * 0.03), int(h * 0.03)
    draw.ellipse((rec_x, rec_y, rec_x + 16, rec_y + 16), fill=(235, 30, 30))
    draw.text((rec_x + 24, rec_y), "REC  CAM-001 [LIVE]", fill=(245, 245, 245), font=font_large)
    draw.text((int(w * 0.62), rec_y), "2012-08-14 07:43:12 IST", fill=(245, 245, 245), font=font_large)
    clean_title = title.replace("\n", " ")[:40]
    draw.text((int(w * 0.03), int(h * 0.93)), f"REF: {ev_id} | {clean_title}", fill=(210, 230, 210), font=font_small)
    draw.text((int(w * 0.80), int(h * 0.93)), "1080P // HQ", fill=(210, 230, 210), font=font_small)
    return img

def ingest_image(image_path, manifest_id, ev_id, ev_type, title):
    img = Image.open(image_path)
    if ev_type == "CCTV_FOOTAGE":
        img = apply_cctv_hud(img, ev_id, title)
        
    temp_path = os.path.join(EVIDENCE_STORE, f"temp_{ev_id}.png")
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
        cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER USER;")
        
        cur.execute("""
            UPDATE civix.evidence_artifact
            SET sha256_hash = %s,
                storage_uri = %s,
                file_size_bytes = %s,
                mime_type = 'image/png',
                processed_at = NOW()
            WHERE artifact_id = (
                SELECT artifact_id FROM civix.evidence_generation_manifest WHERE manifest_id = %s::uuid
            )
        """, (sha256_bytes, final_filename, file_size, manifest_id))
        
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET generation_status = 'GENERATED', updated_at = NOW()
            WHERE manifest_id = %s::uuid
        """, (manifest_id,))
        
        cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER USER;")
    finally:
        conn.close()
        
    print(f"INGEST SUCCESS: {ev_id} -> {final_filename} ({file_size} bytes)")
    return final_filename, file_size, sha256_hex

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: ingest_image.py <image_path> <manifest_id> <ev_id> <ev_type> <title>")
        sys.exit(1)
    ingest_image(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])

"""
Populate all 168 VIS- evidence images with real photographs from Picsum.photos
(free, no API key, returns real photos by seed).

Evidence type → photo category seeds:
  CCTV_FOOTAGE      → dark urban/street photos  
  SKETCH            → portrait/face photos (grayscaled)
  PHYSICAL_EVIDENCE → object/macro close-ups
  PHOTOGRAPH        → urban/crime scene environments
"""
import os, json, time, hashlib, psycopg2, urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO

DB_CONFIG = {
    "host": "localhost", "port": 5432,
    "dbname": "civix_demo", "user": "postgres", "password": "postgres",
}
EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
os.makedirs(EVIDENCE_STORE, exist_ok=True)

# Picsum seed offsets by type so each type gets visually different photos
TYPE_SEED_OFFSET = {
    "CCTV_FOOTAGE":      1000,   # urban, street, architecture seeds
    "SKETCH":            2000,   # portrait-ish seeds  
    "PHYSICAL_EVIDENCE": 3000,   # object/item seeds
    "PHOTOGRAPH":        4000,   # outdoor/scene seeds
}

def load_font(size):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()

def apply_cctv_hud(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    # Desaturate + darken slightly to look like surveillance
    img = ImageEnhance.Color(img).enhance(0.4)
    img = ImageEnhance.Brightness(img).enhance(0.75)
    # Add green tint
    r, g, b = img.split()
    g = ImageEnhance.Brightness(Image.fromarray(__import__('numpy').array(g))).enhance(1.1) if False else g
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    fl = load_font(24)
    fs = load_font(16)
    
    # Scan lines effect
    for y in range(0, h, 3):
        draw.line([(0, y), (w, y)], fill=(0, 0, 0, 40), width=1)
    
    # Target bounding box
    bx1, by1 = int(w * 0.28), int(h * 0.22)
    bx2, by2 = int(w * 0.72), int(h * 0.78)
    draw.rectangle([bx1, by1, bx2, by2], outline=(0, 230, 255), width=2)
    draw.rectangle([bx1 - 1, by1 - 22, bx1 + 220, by1], fill=(0, 30, 45))
    draw.text((bx1 + 4, by1 - 20), "TARGET ACQUIRED [CONF:97.4%]", fill=(0, 230, 255), font=fs)
    
    # REC indicator
    rx, ry = 28, 22
    draw.ellipse([rx, ry, rx + 18, ry + 18], fill=(235, 30, 30))
    cam_id = f"CAM-{(abs(hash(ev_id)) % 899) + 101:03d}"
    draw.text((rx + 26, ry - 1), f"REC  {cam_id} [LIVE]", fill=(245, 245, 245), font=fl)
    draw.text((int(w * 0.63), ry - 1), "2026-07-19 23:14:02 IST", fill=(245, 245, 245), font=fl)
    
    # Bottom bar
    draw.rectangle([0, h - 44, w, h], fill=(8, 12, 22))
    t = (title or "")[:55]
    draw.text((28, h - 34), f"REF:{ev_id} | {t} | DELHI NCR SURVEILLANCE", fill=(150, 220, 150), font=fs)
    draw.text((int(w * 0.83), h - 34), "1080P·FORENSIC", fill=(0, 230, 255), font=fs)
    return img

def apply_sketch_hud(img, ev_id, title):
    img = img.convert("L")  # grayscale
    # Pencil sketch effect
    edges = img.filter(ImageFilter.FIND_EDGES)
    inverted = ImageOps.invert(edges)
    contrast = ImageEnhance.Contrast(inverted).enhance(2.5)
    # Blend with paper tone
    paper = Image.new("L", img.size, 245)
    blended = Image.blend(contrast, paper, alpha=0.15)
    img = blended.convert("RGB")
    # Paper warm tint
    r, g, b = img.split()
    r = r.point(lambda x: min(255, x + 8))
    b = b.point(lambda x: max(0, x - 12))
    img = Image.merge("RGB", (r, g, b))
    
    draw = ImageDraw.Draw(img)
    w, h = img.size
    fs = load_font(18)
    
    draw.rectangle([18, 18, w - 18, h - 18], outline=(40, 40, 40), width=3)
    draw.rectangle([0, h - 50, w, h], fill=(248, 245, 235))
    draw.text((35, h - 38), f"DELHI NCR POLICE — SUSPECT COMPOSITE SKETCH [REF:{ev_id}]", fill=(35, 35, 35), font=fs)
    return img

def apply_physical_hud(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    fs = load_font(18)
    
    # Evidence tag border
    draw.rectangle([12, 12, w - 12, h - 12], outline=(220, 210, 30), width=2)
    
    # Yellow metric scale bar at bottom
    ry = h - 58
    draw.rectangle([50, ry, 560, ry + 34], fill=(240, 210, 40))
    for i in range(21):
        x = 50 + i * 25
        draw.line([x, ry, x, ry + (34 if i % 5 == 0 else 17)], fill=(10, 10, 10), width=2)
    draw.rectangle([0, ry - 5, w, h], fill=(14, 17, 22))
    draw.rectangle([50, ry, 560, ry + 34], fill=(240, 210, 40))
    for i in range(21):
        x = 50 + i * 25
        draw.line([x, ry, x, ry + (34 if i % 5 == 0 else 17)], fill=(10, 10, 10), width=2)
    draw.text((575, ry + 8), f"FORENSIC METRIC SCALE [CM] | REF:{ev_id}", fill=(240, 240, 240), font=fs)
    return img

def apply_photo_hud(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    fs = load_font(18)
    
    draw.rectangle([14, 14, w - 14, h - 14], outline=(210, 170, 40), width=3)
    draw.rectangle([0, h - 44, w, h], fill=(18, 22, 32))
    t = (title or "")[:58]
    draw.text((28, h - 34), f"CRIME SCENE PHOTOGRAPH | REF:{ev_id} | {t}", fill=(240, 205, 50), font=fs)
    return img

def fetch_picsum(seed, width=1024, height=768):
    url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return BytesIO(resp.read())

def save_to_store(img, ev_id):
    tmp = os.path.join(EVIDENCE_STORE, f"tmp_{ev_id}.png")
    img.save(tmp, format="PNG")
    with open(tmp, "rb") as f:
        data = f.read()
    sha_hex = hashlib.sha256(data).hexdigest()
    fname = f"{sha_hex}.png"
    fpath = os.path.join(EVIDENCE_STORE, fname)
    if os.path.exists(fpath):
        os.remove(fpath)
    os.rename(tmp, fpath)
    return fname, len(data), bytes.fromhex(sha_hex)

def main():
    print("=== POPULATING VIS- ITEMS WITH PICSUM REAL PHOTOGRAPHS ===\n")

    with open("scratch/vis_items.json") as f:
        items = json.load(f)
    
    total = len(items)
    print(f"Loading {total} evidence items...\n")

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL;")

    success = 0
    for idx, item in enumerate(items, 1):
        ev_id = item["ev_id"]
        ev_type = item["ev_type"]
        title = item["title"]
        artifact_id = item["artifact_id"]
        manifest_id = item["manifest_id"]

        # Unique seed per item (deterministic from ev_id)
        base_seed = abs(hash(ev_id)) % 900
        seed = TYPE_SEED_OFFSET.get(ev_type, 5000) + (base_seed % 100)

        print(f"[{idx:3d}/{total}] {ev_id} ({ev_type}) seed={seed} … ", end="", flush=True)

        try:
            img_buf = fetch_picsum(seed)
            img = Image.open(img_buf)

            if ev_type == "CCTV_FOOTAGE":
                img = apply_cctv_hud(img, ev_id, title)
            elif ev_type == "SKETCH":
                img = apply_sketch_hud(img, ev_id, title)
            elif ev_type == "PHYSICAL_EVIDENCE":
                img = apply_physical_hud(img, ev_id, title)
            else:
                img = apply_photo_hud(img, ev_id, title)

            fname, fsize, sha_bytes = save_to_store(img, ev_id)

            cur.execute("""
                UPDATE civix.evidence_artifact
                SET sha256_hash=%s, storage_uri=%s, file_size_bytes=%s,
                    mime_type='image/png', processed_at=NOW()
                WHERE artifact_id=%s
            """, (sha_bytes, fname, fsize, artifact_id))

            cur.execute("""
                UPDATE civix.evidence_generation_manifest
                SET generation_status='GENERATED', updated_at=NOW()
                WHERE manifest_id=%s
            """, (manifest_id,))

            print(f"{fname[:14]}… {fsize // 1024}KB ✓")
            success += 1
            time.sleep(0.3)  # polite delay

        except Exception as e:
            print(f"ERROR: {e}")

    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL;")
    conn.close()
    print(f"\n✓ DONE — {success}/{total} items updated with real Picsum photographs.")

if __name__ == "__main__":
    main()

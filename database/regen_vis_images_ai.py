"""
Regenerate all 180 VIS- evidence images using Pollinations AI (Flux model).
Sequential with delay to respect rate limits. Falls back procedurally only if
all AI attempts fail for that item.
"""
import os, sys, time, random, hashlib, psycopg2, urllib.request, urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "civix_demo",
    "user":     "postgres",
    "password": "postgres",
}
EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
os.makedirs(EVIDENCE_STORE, exist_ok=True)

# ── prompt builders ─────────────────────────────────────────────────────────

def build_prompt(ev_id, ev_type, title):
    t = title.strip()
    if ev_type == "CCTV_FOOTAGE":
        return (
            f"Grainy 1080p surveillance CCTV security camera still frame, night time, "
            f"urban street in Delhi India, concrete walls, overhead streetlights, "
            f"suspect person in distance, dark shadows, green-tinted camera noise, "
            f"realistic security footage: {t}. Forensic law enforcement evidence still."
        )
    elif ev_type == "SKETCH":
        return (
            f"Hand-drawn police forensic composite suspect sketch, pencil charcoal on "
            f"white paper, detailed male face, front-facing portrait, Indian police "
            f"forensics department: {t}. Monochrome pencil drawing."
        )
    elif ev_type == "PHYSICAL_EVIDENCE":
        return (
            f"Macro photograph of forensic physical evidence item on dark crime lab "
            f"table, professional evidence lighting, sharp focus, Indian police crime "
            f"laboratory setting: {t}."
        )
    else:  # PHOTOGRAPH
        return (
            f"Authentic crime scene field photograph, DSLR camera, realistic lighting, "
            f"Indian police investigation, Delhi NCR urban environment: {t}."
        )

# ── HUD overlays ─────────────────────────────────────────────────────────────

def load_fonts(h):
    try:
        return ImageFont.truetype("arial.ttf", max(14, int(h * 0.032))), \
               ImageFont.truetype("arial.ttf", max(12, int(h * 0.022)))
    except Exception:
        d = ImageFont.load_default()
        return d, d

def hud_cctv(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    ImageEnhance.Color(img).enhance(0.78)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    fl, fs = load_fonts(h)
    cam_id = f"CAM-{(abs(hash(ev_id)) % 899) + 101:03d}"
    ts = "2026-07-19 23:14:02 IST"
    # bounding box
    bx1, by1, bx2, by2 = int(w*.3), int(h*.25), int(w*.7), int(h*.76)
    draw.rectangle([bx1,by1,bx2,by2], outline=(0,230,255), width=2)
    draw.rectangle([bx1-1, by1-22, bx1+210, by1], fill=(0,30,45))
    draw.text((bx1+4, by1-20), "TARGET DETECTED [CONF:96.8%]", fill=(0,230,255), font=fs)
    # REC dot
    rx, ry = 28, 22
    draw.ellipse([rx, ry, rx+18, ry+18], fill=(235,30,30))
    draw.text((rx+24, ry-1), f"REC  {cam_id} [LIVE]", fill=(245,245,245), font=fl)
    draw.text((int(w*.64), ry-1), ts, fill=(245,245,245), font=fl)
    # bottom bar
    draw.rectangle([0, h-42, w, h], fill=(8,12,22))
    t = (title or "")[:50]
    draw.text((28, h-32), f"REF:{ev_id} | {t} | DELHI NCR SURVEILLANCE", fill=(200,230,200), font=fs)
    draw.text((int(w*.82), h-32), "1080P·FORENSIC", fill=(0,230,255), font=fs)
    return img

def hud_sketch(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    _, fs = load_fonts(h)
    draw.rectangle([18,18,w-18,h-18], outline=(40,40,40), width=3)
    draw.rectangle([0,h-50,w,h], fill=(245,243,235))
    draw.text((35, h-38), f"DELHI NCR POLICE — SUSPECT COMPOSITE SKETCH [REF:{ev_id}]", fill=(35,35,35), font=fs)
    return img

def hud_physical(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    _, fs = load_fonts(h)
    ry = h - 55
    draw.rectangle([50, ry, 550, ry+32], fill=(240,210,40))
    for i in range(21):
        x = 50 + i * 25
        draw.line([x,ry, x, ry+(32 if i%5==0 else 16)], fill=(10,10,10), width=2)
    draw.text((565, ry+7), f"FORENSIC METRIC SCALE [CM] | REF:{ev_id}", fill=(245,245,245), font=fs)
    return img

def hud_photo(img, ev_id, title):
    img = img.convert("RGB").resize((1024, 768), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(img)
    w, h = img.size
    _, fs = load_fonts(h)
    draw.rectangle([14,14,w-14,h-14], outline=(210,170,40), width=3)
    draw.rectangle([0, h-44, w, h], fill=(18,22,32))
    t = (title or "")[:55]
    draw.text((28, h-34), f"CRIME SCENE PHOTOGRAPH | REF:{ev_id} | {t}", fill=(240,205,50), font=fs)
    return img

def apply_hud(img, ev_id, ev_type, title):
    if ev_type == "CCTV_FOOTAGE":   return hud_cctv(img, ev_id, title)
    if ev_type == "SKETCH":         return hud_sketch(img, ev_id, title)
    if ev_type == "PHYSICAL_EVIDENCE": return hud_physical(img, ev_id, title)
    return hud_photo(img, ev_id, title)

# ── procedural fallback ───────────────────────────────────────────────────────

def procedural_img(ev_id, ev_type):
    w, h = 1024, 768
    if ev_type == "CCTV_FOOTAGE":
        img = Image.new("RGB", (w,h), (16,20,30))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            r,g,b = int(10+(y/h)*14), int(14+(y/h)*18), int(22+(y/h)*24)
            draw.line([(0,y),(w,y)], fill=(r,g,b))
        for x in range(0,w,64): draw.line([(x,0),(x,h)], fill=(30,40,52), width=1)
        for y in range(0,h,64): draw.line([(0,y),(w,y)], fill=(30,40,52), width=1)
    elif ev_type == "SKETCH":
        img = Image.new("RGB", (w,h), (242,240,232))
        draw = ImageDraw.Draw(img)
        for i in range(0,w,40): draw.line([(i,0),(i,h)], fill=(228,225,215), width=1)
        cx,cy = 512,360
        draw.ellipse([cx-130,cy-170,cx+130,cy+180], outline=(35,35,35), width=4)
        draw.ellipse([cx-75,cy-35,cx-20,cy-10], outline=(35,35,35), width=3)
        draw.ellipse([cx+20,cy-35,cx+75,cy-10], outline=(35,35,35), width=3)
        draw.line([(cx,cy-10),(cx-15,cy+50),(cx+10,cy+55)], fill=(35,35,35), width=3)
        draw.line([(cx-45,cy+95),(cx+45,cy+95)], fill=(35,35,35), width=4)
    elif ev_type == "PHYSICAL_EVIDENCE":
        img = Image.new("RGB", (w,h), (14,17,22))
        draw = ImageDraw.Draw(img)
        draw.rectangle([280,200,744,520], fill=(42,52,65), outline=(100,120,145), width=3)
        draw.text((300,220), f"EVIDENCE: {ev_id}", fill=(200,225,245))
    else:
        img = Image.new("RGB", (w,h), (24,30,42))
        draw = ImageDraw.Draw(img)
        draw.rectangle([80,80,944,688], outline=(210,170,40), width=4)
        draw.text((100,100), f"CRIME SCENE PHOTOGRAPH | {ev_id}", fill=(240,205,50))
    return img

# ── AI fetch ─────────────────────────────────────────────────────────────────

def fetch_ai(prompt, ev_id, retries=3, timeout=25):
    seed = (abs(hash(ev_id)) % 999999) + 1
    encoded = urllib.parse.quote(prompt)
    for model in ["flux", "turbo"]:
        url = (f"https://image.pollinations.ai/prompt/{encoded}"
               f"?width=1024&height=768&nologo=true&seed={seed}&model={model}")
        for attempt in range(retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read()
                    if len(data) > 10000:
                        return data
            except Exception as e:
                wait = (2 ** attempt) + random.uniform(0.5, 2)
                time.sleep(wait)
    return None

# ── save + commit ─────────────────────────────────────────────────────────────

def save_and_commit(cur, artifact_id, manifest_id, img, ev_id):
    tmp = os.path.join(EVIDENCE_STORE, f"tmp_{ev_id}.png")
    img.save(tmp, format="PNG")
    with open(tmp, "rb") as f:
        data = f.read()
    sha_hex = hashlib.sha256(data).hexdigest()
    fname = f"{sha_hex}.png"
    fpath = os.path.join(EVIDENCE_STORE, fname)
    if os.path.exists(fpath): os.remove(fpath)
    os.rename(tmp, fpath)
    sha_bytes = bytes.fromhex(sha_hex)
    cur.execute("""
        UPDATE civix.evidence_artifact
        SET sha256_hash=%s, storage_uri=%s, file_size_bytes=%s,
            mime_type='image/png', processed_at=NOW()
        WHERE artifact_id=%s
    """, (sha_bytes, fname, len(data), artifact_id))
    cur.execute("""
        UPDATE civix.evidence_generation_manifest
        SET generation_status='GENERATED', updated_at=NOW()
        WHERE manifest_id=%s
    """, (manifest_id,))
    return fname, len(data)

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    print("=== REGENERATING 180 VIS- IMAGES WITH REAL AI (POLLINATIONS FLUX) ===\n")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL;")

    cur.execute("""
        SELECT a.artifact_id, m.manifest_id, m.evidence_id_str,
               m.evidence_type, m.title
        FROM civix.evidence_artifact a
        JOIN civix.evidence_generation_manifest m ON a.artifact_id = m.artifact_id
        WHERE a.mime_type LIKE 'image/%%'
          AND m.evidence_id_str LIKE 'VIS-%%'
        ORDER BY m.evidence_id_str;
    """)
    rows = cur.fetchall()
    total = len(rows)
    print(f"Items to process: {total}\n")

    ai_count = 0
    for idx, (artifact_id, manifest_id, ev_id, ev_type, title) in enumerate(rows, 1):
        prompt = build_prompt(ev_id, ev_type, title)
        print(f"[{idx:3d}/{total}] {ev_id} ({ev_type}) … ", end="", flush=True)

        img_data = fetch_ai(prompt, ev_id)
        if img_data:
            tmp = os.path.join(EVIDENCE_STORE, f"tmp_{ev_id}.png")
            with open(tmp, "wb") as f: f.write(img_data)
            try:
                img = Image.open(tmp)
            except Exception:
                img = procedural_img(ev_id, ev_type)
            ai_count += 1
            src = "AI"
        else:
            img = procedural_img(ev_id, ev_type)
            src = "PROC"

        img = apply_hud(img, ev_id, ev_type, title)
        fname, fsize = save_and_commit(cur, artifact_id, manifest_id, img, ev_id)
        print(f"{fname[:16]}… {fsize//1024}KB [{src}]")

        # Rate-limit: 2s between AI items, 0.2s between procedural
        time.sleep(2.0 if src == "AI" else 0.2)

    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL;")
    conn.close()
    print(f"\n✓ DONE — {total} images committed. {ai_count} AI-generated, {total-ai_count} procedural fallback.")

if __name__ == "__main__":
    main()

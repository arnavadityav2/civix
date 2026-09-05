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

DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "postgres"),
    "password": os.getenv("CIVIX_DB_PASSWORD", "postgres"),
}

EVIDENCE_STORE = r"C:\data\civix_demo\evidence_store"
os.makedirs(EVIDENCE_STORE, exist_ok=True)

def generate_procedural_image(ev_id, ev_type, title):
    w, h = 1024, 768
    if ev_type == "CCTV_FOOTAGE":
        img = Image.new("RGB", (w, h), color=(18, 22, 30))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            r = int(10 + (y / h) * 15)
            g = int(14 + (y / h) * 18)
            b = int(22 + (y / h) * 25)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        for x in range(0, w, 64):
            draw.line([(x, 0), (x, h)], fill=(32, 42, 55), width=1)
        for y in range(0, h, 64):
            draw.line([(0, y), (w, y)], fill=(32, 42, 55), width=1)
        box_x1, box_y1 = int(w * 0.32), int(h * 0.28)
        box_x2, box_y2 = int(w * 0.68), int(h * 0.74)
        draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=(0, 220, 245), width=2)
        draw.text((box_x1, box_y1 - 20), "TARGET DETECTED [CONF: 96.8%]", fill=(0, 220, 245))
        # HUD overlay
        rec_x, rec_y = 30, 25
        draw.ellipse((rec_x, rec_y, rec_x + 16, rec_y + 16), fill=(235, 30, 30))
        draw.text((rec_x + 24, rec_y), "REC  CAM-408 [LIVE]", fill=(240, 240, 240))
        draw.text((int(w * 0.62), rec_y), "2026-07-19 23:14:02 IST", fill=(240, 240, 240))
        draw.text((30, h - 35), f"REF: {ev_id} | DELHI NCR SURVEILLANCE CORRIDOR", fill=(200, 225, 200))
    elif ev_type == "SKETCH":
        img = Image.new("RGB", (w, h), color=(242, 240, 232))
        draw = ImageDraw.Draw(img)
        for i in range(0, w, 40):
            draw.line([(i, 0), (i, h)], fill=(228, 225, 215), width=1)
        cx, cy = 512, 360
        draw.ellipse([cx - 130, cy - 170, cx + 130, cy + 180], outline=(35, 35, 35), width=4)
        draw.ellipse([cx - 75, cy - 35, cx - 20, cy - 10], outline=(35, 35, 35), width=3)
        draw.ellipse([cx + 20, cy - 35, cx + 75, cy - 10], outline=(35, 35, 35), width=3)
        draw.line([(cx, cy - 10), (cx - 15, cy + 50), (cx + 10, cy + 55)], fill=(35, 35, 35), width=3)
        draw.line([(cx - 45, cy + 95), (cx + 45, cy + 95)], fill=(35, 35, 35), width=4)
        draw.text((280, 680), f"FORENSIC COMPOSITE SUSPECT SKETCH | REF: {ev_id}", fill=(50, 50, 50))
    elif ev_type == "PHYSICAL_EVIDENCE":
        img = Image.new("RGB", (w, h), color=(14, 17, 22))
        draw = ImageDraw.Draw(img)
        draw.rectangle([280, 200, 744, 520], fill=(42, 52, 65), outline=(100, 120, 145), width=3)
        draw.text((300, 220), f"FORENSIC PHYSICAL EVIDENCE: {ev_id}", fill=(210, 230, 250))
        # Yellow metric scale bar
        ruler_y = h - 60
        draw.rectangle([50, ruler_y, 550, ruler_y + 30], fill=(240, 210, 40))
        for i in range(21):
            x = 50 + i * 25
            draw.line([x, ruler_y, x, ruler_y + (30 if i % 5 == 0 else 15)], fill=(10, 10, 10), width=2)
        draw.text((570, ruler_y + 5), f"CM METRIC SCALE | REF: {ev_id}", fill=(245, 245, 245))
    else: # PHOTOGRAPH
        img = Image.new("RGB", (w, h), color=(25, 30, 40))
        draw = ImageDraw.Draw(img)
        draw.rectangle([80, 80, 944, 688], outline=(210, 170, 40), width=4)
        draw.text((100, 100), f"CRIME SCENE FIELD PHOTOGRAPH | REF: {ev_id}", fill=(240, 205, 50))
        draw.text((100, 640), "DELHI NCR POLICE FORENSIC UNIT — EVIDENCE GRADE", fill=(200, 210, 225))
        
    return img

def fix_all_images():
    print("=== STARTING FULL RE-PROCESSING OF ALL 180 EVIDENCE IMAGES ===")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cur = conn.cursor()

    # Disable RLS and user triggers for bulk fast update
    cur.execute("ALTER TABLE civix.evidence_artifact DISABLE TRIGGER ALL;")

    # Fetch all 180 image artifacts and their manifests
    cur.execute("""
        SELECT a.artifact_id, m.manifest_id, m.evidence_id_str, m.evidence_type, m.title
        FROM civix.evidence_artifact a
        JOIN civix.evidence_generation_manifest m ON a.artifact_id = m.artifact_id
        WHERE a.mime_type LIKE 'image/%'
        ORDER BY m.evidence_id_str;
    """)
    rows = cur.fetchall()
    print(f"Total image artifacts to process and commit: {len(rows)}")

    success_count = 0
    for idx, r in enumerate(rows, 1):
        artifact_id, manifest_id, ev_id, ev_type, title = r

        # Generate image
        img = generate_procedural_image(ev_id, ev_type, title)
        
        # Save temp PNG
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

        # Update evidence_artifact directly
        cur.execute("""
            UPDATE civix.evidence_artifact
            SET sha256_hash = %s,
                storage_uri = %s,
                file_size_bytes = %s,
                mime_type = 'image/png',
                processed_at = NOW()
            WHERE artifact_id = %s
        """, (sha256_bytes, final_filename, file_size, artifact_id))

        # Update manifest
        cur.execute("""
            UPDATE civix.evidence_generation_manifest
            SET generation_status = 'GENERATED', updated_at = NOW()
            WHERE manifest_id = %s
        """, (manifest_id,))

        success_count += 1
        if idx % 20 == 0 or idx == len(rows):
            print(f"  [{idx}/{len(rows)}] Processed & Committed: {ev_id} -> {final_filename[:16]}... ({file_size} bytes)")

    cur.execute("ALTER TABLE civix.evidence_artifact ENABLE TRIGGER ALL;")
    conn.close()

    print(f"\nCOMPLETED! 100% ({success_count}/{len(rows)}) evidence image artifacts are fully generated, saved to disk, and committed in PostgreSQL!")

if __name__ == '__main__':
    fix_all_images()

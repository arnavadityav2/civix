"""
CIVIX 2.0 — Biometric Demo Index Generator
Phase 3 + 4 + 5: Reference preparation, embedding generation, and calibration.

This script:
1. Reads the cohort manifest (scratch/biometric_demo_cohort.json)
2. Copies each person's avatar as the 'clear' reference
3. Generates CCTV-style derived variants via OpenCV transforms
4. Detects faces and generates 128-dim SFace embeddings
5. Computes same-person and different-person similarity distributions
6. Determines empirical threshold and ambiguity margin
7. Writes:
   - C:\data\civix_demo\biometric_demo\index.json
   - C:\data\civix_demo\biometric_demo\embeddings.npz
   - C:\data\civix_demo\biometric_demo\biometric_config.json

Transforms used for CCTV-style variants (marked is_derived=true):
  ref-001: clear reference (from avatar, is_derived=false)
  ref-002: slight gaussian blur
  ref-003: low-light (brightness/contrast)
  ref-004: partial occlusion (top third darkened)
  ref-005: slight rotation
  ref-006: JPEG compression degradation
  ref-007: noise / grain
  ref-008: horizontal flip (different angle appearance)
  ref-009: crop + resize (zoom simulation)
  ref-010: combined noise+blur (CCTV night-mode)
  ref-011: contrast enhancement (overexposed flash)
  ref-012: side-tilt (head tilt simulation)

DATA INTEGRITY:
- This script only READS from PostgreSQL (via cohort.json entity_id + avatar_url).
- It never writes to any civix.* table.
- All outputs go to C:\data\civix_demo\biometric_demo\

Usage:
    python scratch/generate_biometric_index.py
"""
import asyncio
import sys
import json
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ============================================================
# CONFIG
# ============================================================
COHORT_PATH = Path(__file__).resolve().parent / "biometric_demo_cohort.json"
BIOMETRIC_ROOT = Path(r"C:\data\civix_demo\biometric_demo")
REFS_DIR = BIOMETRIC_ROOT / "refs"
MODELS_DIR = BIOMETRIC_ROOT / "models"
INDEX_PATH = BIOMETRIC_ROOT / "index.json"
EMBEDDINGS_PATH = BIOMETRIC_ROOT / "embeddings.npz"
CONFIG_PATH = BIOMETRIC_ROOT / "biometric_config.json"

YUNET_PATH = MODELS_DIR / "face_detection_yunet_2023mar.onnx"
SFACE_PATH = MODELS_DIR / "face_recognition_sface_2021dec.onnx"

# Avatar source root
AVATAR_SRC = Path(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\frontend\public\assets\avatars")

DETECTOR_SCORE_THRESHOLD = 0.5  # Lower for reference images (known good)
DETECTOR_NMS_THRESHOLD = 0.3

# ============================================================
# CCTV-STYLE TRANSFORMS (deterministic, marked is_derived=true)
# ============================================================

def make_variants(img: np.ndarray) -> list[tuple[str, np.ndarray, str]]:
    """
    Returns list of (variant_name, image_array, quality_note)
    """
    variants = []
    h, w = img.shape[:2]

    # ref-002: Slight blur
    blurred = cv2.GaussianBlur(img, (5, 5), 1.2)
    variants.append(("ref-002", blurred, "slight_blur"))

    # ref-003: Low-light
    low_light = cv2.convertScaleAbs(img, alpha=0.55, beta=-20)
    variants.append(("ref-003", low_light, "low_light"))

    # ref-004: Partial occlusion (top third obscured with dark rectangle)
    occluded = img.copy()
    cv2.rectangle(occluded, (int(w*0.1), 0), (int(w*0.6), int(h*0.35)), (20, 20, 20), -1)
    variants.append(("ref-004", occluded, "partial_occlusion"))

    # ref-005: Slight rotation (5 degrees)
    M = cv2.getRotationMatrix2D((w//2, h//2), 8, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    variants.append(("ref-005", rotated, "slight_rotation"))

    # ref-006: JPEG compression degradation
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 25]
    _, enc = cv2.imencode('.jpg', img, encode_param)
    compressed = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    variants.append(("ref-006", compressed, "jpeg_compression"))

    # ref-007: Noise / grain
    noise = np.random.randint(-30, 30, img.shape, dtype=np.int16)
    noisy = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    variants.append(("ref-007", noisy, "noise_grain"))

    # ref-008: Crop + resize (zoom simulation)
    margin = int(min(h, w) * 0.15)
    cropped = img[margin:h-margin, margin:w-margin]
    zoomed = cv2.resize(cropped, (w, h))
    variants.append(("ref-008", zoomed, "zoom_crop"))

    # ref-009: Combined noise + blur (CCTV night-mode)
    night = cv2.convertScaleAbs(img, alpha=0.45, beta=-30)
    night = cv2.GaussianBlur(night, (7, 7), 2.0)
    noise2 = np.random.randint(-20, 20, night.shape, dtype=np.int16)
    night = np.clip(night.astype(np.int16) + noise2, 0, 255).astype(np.uint8)
    variants.append(("ref-009", night, "night_mode_cctv"))

    # ref-010: Contrast enhancement (overexposed)
    overexposed = cv2.convertScaleAbs(img, alpha=1.6, beta=40)
    variants.append(("ref-010", overexposed, "overexposed"))

    # ref-011: Head tilt simulation (12 degree rotation)
    M2 = cv2.getRotationMatrix2D((w//2, h//2), 15, 0.92)
    tilted = cv2.warpAffine(img, M2, (w, h), borderMode=cv2.BORDER_REPLICATE)
    variants.append(("ref-011", tilted, "head_tilt"))

    # ref-012: Strong blur (distant CCTV)
    heavy_blur = cv2.GaussianBlur(img, (11, 11), 3.5)
    variants.append(("ref-012", heavy_blur, "heavy_blur_distant"))

    return variants


def init_models():
    detector = cv2.FaceDetectorYN.create(
        str(YUNET_PATH), '', (320, 320),
        DETECTOR_SCORE_THRESHOLD, DETECTOR_NMS_THRESHOLD, 5000,
    )
    recognizer = cv2.FaceRecognizerSF.create(str(SFACE_PATH), '')
    return detector, recognizer


def detect_and_embed(img: np.ndarray, detector, recognizer) -> tuple[np.ndarray | None, list | None, float | None]:
    """
    Returns (embedding float32[128], bounding_box_list, confidence_score)
    or (None, None, None) if no face detected.
    """
    h, w = img.shape[:2]
    detector.setInputSize((w, h))
    _, faces = detector.detect(img)

    if faces is None or len(faces) == 0:
        return None, None, None

    # Take highest-confidence face
    best_face = faces[0]
    confidence = float(best_face[-1])
    bbox = best_face[:4].tolist()

    aligned = recognizer.alignCrop(img, best_face)
    feature = recognizer.feature(aligned)  # shape (1, 128)

    # L2 normalize
    feat_flat = feature.flatten().astype(np.float32)
    norm = np.linalg.norm(feat_flat)
    if norm > 0:
        feat_flat = feat_flat / norm

    return feat_flat, bbox, confidence


def main():
    print("=" * 70)
    print("  CIVIX 2.0 — BIOMETRIC INDEX GENERATOR")
    print("=" * 70)

    # Load cohort
    with open(COHORT_PATH) as f:
        cohort = json.load(f)

    all_persons = cohort["investigative_subjects"] + cohort["civilians"]
    print(f"\nCohort size: {len(all_persons)} persons")

    # Init models
    print("\nLoading face models...")
    detector, recognizer = init_models()
    print("  YuNet 2023mar: LOADED")
    print("  SFace 2021dec: LOADED")

    # Create directory structure
    REFS_DIR.mkdir(parents=True, exist_ok=True)

    index_entries = []
    embeddings_dict = {}  # key -> np.ndarray float32[128]

    failed_persons = []

    for person in all_persons:
        entity_id = person["entity_id"]
        display_name = person["display_name"]
        avatar_url = person.get("avatar_url", "")

        print(f"\n--- {display_name} ({entity_id[:8]}) ---")

        person_dir = REFS_DIR / entity_id
        person_dir.mkdir(exist_ok=True)

        # Find avatar image
        avatar_path = None
        if avatar_url:
            rel = avatar_url.lstrip("/")
            src = Path(r"c:\Users\ARNAV ADITYA\Desktop\civix 2.0\frontend\public") / rel
            if src.exists():
                avatar_path = src
            else:
                # Try avatars dir directly
                filename = Path(avatar_url).name
                candidate = AVATAR_SRC / filename
                if candidate.exists():
                    avatar_path = candidate

        if avatar_path is None:
            # Try by entity_id pattern
            for ext in [".webp", ".jpg", ".png"]:
                candidate = AVATAR_SRC / f"{entity_id}{ext}"
                if candidate.exists():
                    avatar_path = candidate
                    break

        if avatar_path is None:
            print(f"  WARNING: No avatar found for {display_name}")
            failed_persons.append(entity_id)
            continue

        # Copy clear reference image
        ref001_dst = person_dir / "ref-001.webp"
        if not ref001_dst.exists():
            shutil.copy2(str(avatar_path), str(ref001_dst))

        # Load the image for processing
        img = cv2.imread(str(avatar_path), cv2.IMREAD_COLOR)
        if img is None:
            print(f"  ERROR: Could not load image at {avatar_path}")
            failed_persons.append(entity_id)
            continue

        # Upscale if too small (avatars are small webp)
        h, w = img.shape[:2]
        if max(h, w) < 200:
            scale = 200.0 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        # Detect face in clear reference
        clear_emb, clear_bbox, clear_conf = detect_and_embed(img, detector, recognizer)
        if clear_emb is None:
            print(f"  WARNING: No face detected in clear reference image (score threshold may be too high). Lowering threshold...")
            # Retry with lower threshold
            detector_low = cv2.FaceDetectorYN.create(
                str(YUNET_PATH), '', (img.shape[1], img.shape[0]),
                0.2, 0.3, 5000,
            )
            detector_low.setInputSize((img.shape[1], img.shape[0]))
            _, faces_low = detector_low.detect(img)
            if faces_low is not None and len(faces_low) > 0:
                best_face = faces_low[0]
                aligned = recognizer.alignCrop(img, best_face)
                feature = recognizer.feature(aligned)
                clear_emb = feature.flatten().astype(np.float32)
                norm = np.linalg.norm(clear_emb)
                if norm > 0:
                    clear_emb = clear_emb / norm
                clear_bbox = best_face[:4].tolist()
                clear_conf = float(best_face[-1])
            else:
                print(f"  SKIP: No face in image for {display_name}")
                failed_persons.append(entity_id)
                continue

        print(f"  Clear reference: face detected, conf={clear_conf:.2f}")

        # Add clear reference to index
        ref_id = f"{entity_id}_ref-001"
        index_entries.append({
            "ref_id": ref_id,
            "person_id": entity_id,
            "image_path": f"refs/{entity_id}/ref-001.webp",
            "source_type": "CLEAR_REFERENCE",
            "is_derived": False,
            "quality_note": "clear_frontal",
            "capture_timestamp": "SYNTHETIC_DEMO_DATA",
            "camera_location": "CIVIX_DEMO_REFERENCE",
            "provenance": "CIVIX_SYNTHETIC_BIOMETRIC_DEMO",
            "embedding_key": ref_id,
            "embedding_model": "SFace",
            "embedding_model_version": "face_recognition_sface_2021dec.onnx",
            "embedding_dim": 128,
            "detection_confidence": round(clear_conf, 4),
        })
        embeddings_dict[ref_id] = clear_emb

        # Generate and embed derived variants
        variants = make_variants(img)
        successful_variants = 0

        for variant_name, var_img, quality_note in variants:
            var_dst = person_dir / f"{variant_name}.webp"
            cv2.imwrite(str(var_dst), var_img)

            var_emb, var_bbox, var_conf = detect_and_embed(var_img, detector, recognizer)
            if var_emb is None:
                # Try lower threshold for tricky variants
                detector_low = cv2.FaceDetectorYN.create(
                    str(YUNET_PATH), '', (var_img.shape[1], var_img.shape[0]),
                    0.2, 0.3, 5000,
                )
                detector_low.setInputSize((var_img.shape[1], var_img.shape[0]))
                _, faces_v = detector_low.detect(var_img)
                if faces_v is not None and len(faces_v) > 0:
                    aligned = recognizer.alignCrop(var_img, faces_v[0])
                    feature = recognizer.feature(aligned)
                    var_emb = feature.flatten().astype(np.float32)
                    norm = np.linalg.norm(var_emb)
                    if norm > 0:
                        var_emb = var_emb / norm
                    var_conf = float(faces_v[0][-1])

            if var_emb is None:
                print(f"    {variant_name}: no face (skipped)")
                os.remove(str(var_dst))
                continue

            var_ref_id = f"{entity_id}_{variant_name}"
            index_entries.append({
                "ref_id": var_ref_id,
                "person_id": entity_id,
                "image_path": f"refs/{entity_id}/{variant_name}.webp",
                "source_type": "DERIVED_CCTV_STYLE",
                "is_derived": True,
                "quality_note": quality_note,
                "capture_timestamp": "SYNTHETIC_DEMO_DATA",
                "camera_location": "CIVIX_SYNTHETIC_BIOMETRIC_DEMO",
                "provenance": "CIVIX_SYNTHETIC_BIOMETRIC_DEMO",
                "embedding_key": var_ref_id,
                "embedding_model": "SFace",
                "embedding_model_version": "face_recognition_sface_2021dec.onnx",
                "embedding_dim": 128,
                "detection_confidence": round(float(var_conf), 4) if var_conf else 0.0,
            })
            embeddings_dict[var_ref_id] = var_emb
            successful_variants += 1

        print(f"  Enrolled: 1 clear + {successful_variants} derived references")

    print(f"\n{'='*70}")
    print(f"EMBEDDING SUMMARY")
    print(f"  Persons processed: {len(all_persons) - len(failed_persons)}/{len(all_persons)}")
    print(f"  Total embeddings: {len(embeddings_dict)}")
    if failed_persons:
        print(f"  Failed persons: {failed_persons}")

    # ============================================================
    # CALIBRATION
    # ============================================================
    print(f"\n{'='*70}")
    print("CALIBRATION")

    # Group embeddings by person
    person_embeddings = {}
    for entry in index_entries:
        pid = entry["person_id"]
        key = entry["embedding_key"]
        if pid not in person_embeddings:
            person_embeddings[pid] = []
        if key in embeddings_dict:
            person_embeddings[pid].append(embeddings_dict[key])

    same_person_scores = []
    diff_person_scores = []
    person_ids = list(person_embeddings.keys())

    for i, pid1 in enumerate(person_ids):
        embs1 = person_embeddings[pid1]
        # Same-person pairs
        for j in range(len(embs1)):
            for k in range(j+1, len(embs1)):
                score = float(np.dot(embs1[j], embs1[k]))
                same_person_scores.append(score)

        # Different-person pairs
        for pid2 in person_ids[i+1:]:
            embs2 = person_embeddings[pid2]
            for e1 in embs1:
                for e2 in embs2:
                    score = float(np.dot(e1, e2))
                    diff_person_scores.append(score)

    same = np.array(same_person_scores)
    diff = np.array(diff_person_scores)

    print(f"\nSame-person pairs:  {len(same)}")
    print(f"Diff-person pairs:  {len(diff)}")

    if len(same) > 0 and len(diff) > 0:
        print(f"\nSame-person similarity:  min={same.min():.3f}, mean={same.mean():.3f}, max={same.max():.3f}, p10={np.percentile(same, 10):.3f}")
        print(f"Diff-person similarity:  min={diff.min():.3f}, mean={diff.mean():.3f}, max={diff.max():.3f}, p90={np.percentile(diff, 90):.3f}")

        # Threshold: midpoint between same-person p10 and diff-person p90
        same_p10 = float(np.percentile(same, 10))
        diff_p90 = float(np.percentile(diff, 90))
        threshold = round((same_p10 + diff_p90) / 2.0, 3)

        # Ambiguity margin: 10% of the gap
        gap = same_p10 - diff_p90
        margin = round(max(gap * 0.15, 0.04), 3)

        print(f"\nCalibrated threshold:    {threshold}")
        print(f"Ambiguity margin:        ±{margin}")

        # Define confidence bands
        high_threshold = round(threshold + (float(same.mean()) - threshold) * 0.5, 3)
        print(f"\nConfidence bands:")
        print(f"  HIGH:    score >= {high_threshold}")
        print(f"  MEDIUM:  score >= {threshold}")
        print(f"  LOW:     score >= {threshold - margin}")
        print(f"  UNCERTAIN: score < {threshold - margin}")
    else:
        threshold = 0.35
        margin = 0.05
        high_threshold = 0.50
        print("WARNING: Not enough data for calibration. Using conservative defaults.")

    # ============================================================
    # WRITE OUTPUTS
    # ============================================================

    # index.json
    index_data = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "CIVIX_SYNTHETIC_BIOMETRIC_DEMO",
        "disclaimer": "These are synthetic demonstration identities. No real persons are enrolled. All CCTV-style images are generated from existing avatars using OpenCV transforms.",
        "models": {
            "detector": "face_detection_yunet_2023mar.onnx",
            "detector_source": "OpenCV Zoo (github.com/opencv/opencv_zoo)",
            "detector_license": "Apache 2.0",
            "recognizer": "face_recognition_sface_2021dec.onnx",
            "recognizer_source": "OpenCV Zoo (github.com/opencv/opencv_zoo)",
            "recognizer_license": "Apache 2.0",
            "embedding_dim": 128,
        },
        "cohort": {
            "total_persons": len(all_persons),
            "enrolled_persons": len(all_persons) - len(failed_persons),
            "investigative_subjects": len(cohort["investigative_subjects"]),
            "civilians": len(cohort["civilians"]),
            "person_ids": [p["entity_id"] for p in all_persons if p["entity_id"] not in failed_persons],
        },
        "entries": index_entries,
    }

    with open(INDEX_PATH, "w") as f:
        json.dump(index_data, f, indent=2)
    print(f"\nWrote: {INDEX_PATH}")

    # embeddings.npz
    np.savez_compressed(str(EMBEDDINGS_PATH), **{k: v for k, v in embeddings_dict.items()})
    print(f"Wrote: {EMBEDDINGS_PATH} ({len(embeddings_dict)} embeddings)")

    # biometric_config.json
    config = {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": "SFace",
        "model_file": "face_recognition_sface_2021dec.onnx",
        "model_source": "OpenCV Zoo",
        "model_license": "Apache 2.0",
        "model_version": "2021dec",
        "embedding_dim": 128,
        "threshold": threshold,
        "ambiguity_margin": margin,
        "high_confidence_threshold": high_threshold,
        "calibrated_at": datetime.now(timezone.utc).isoformat(),
        "cohort_size": len(all_persons) - len(failed_persons),
        "reference_count": len(embeddings_dict),
        "same_person_stats": {
            "count": int(len(same)),
            "min": round(float(same.min()), 4) if len(same) > 0 else None,
            "mean": round(float(same.mean()), 4) if len(same) > 0 else None,
            "max": round(float(same.max()), 4) if len(same) > 0 else None,
            "p10": round(float(np.percentile(same, 10)), 4) if len(same) > 0 else None,
        },
        "diff_person_stats": {
            "count": int(len(diff)),
            "min": round(float(diff.min()), 4) if len(diff) > 0 else None,
            "mean": round(float(diff.mean()), 4) if len(diff) > 0 else None,
            "max": round(float(diff.max()), 4) if len(diff) > 0 else None,
            "p90": round(float(np.percentile(diff, 90)), 4) if len(diff) > 0 else None,
        },
        "confidence_bands": {
            "HIGH": f">= {high_threshold}",
            "MEDIUM": f">= {threshold}",
            "LOW": f">= {threshold - margin}",
            "UNCERTAIN": f"< {threshold - margin}"
        }
    }

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    print(f"Wrote: {CONFIG_PATH}")

    print(f"\n{'='*70}")
    print("INDEX GENERATION COMPLETE")
    print(f"  Total index entries: {len(index_entries)}")
    print(f"  Total embeddings: {len(embeddings_dict)}")
    print(f"  Threshold: {threshold}")
    print(f"  Ambiguity margin: {margin}")
    print("="*70)


if __name__ == "__main__":
    main()

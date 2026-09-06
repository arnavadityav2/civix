import os
import sys
import cv2
import numpy as np
from pathlib import Path

data_dir = Path(r"C:\data\civix_demo\biometric_demo")
models_dir = data_dir / "models"
yunet_path = models_dir / "face_detection_yunet_2023mar.onnx"
sface_path = models_dir / "face_recognition_sface_2021dec.onnx"

print(f"Model Path (Detection) : {yunet_path}")
print(f"Model Path (Recognition): {sface_path}")
print(f"Detection Model Exists  : {yunet_path.exists()}")
print(f"Recognition Model Exists: {sface_path.exists()}")

# Find sample images
refs_dir = data_dir / "refs"
sample_images = []
for p in refs_dir.glob("*/*.webp"):
    sample_images.append(str(p))

print(f"Found {len(sample_images)} reference images.")

def run_debug_detection(image_path: str, score_thresh: float = 0.6, nms_thresh: float = 0.3):
    img = cv2.imread(image_path)
    if img is None:
        print(f"ERROR: Unable to read image {image_path}")
        return
    
    h, w = img.shape[:2]
    print(f"\n==================================================")
    print(f"IMAGE: {Path(image_path).name} ({w}x{h})")
    
    # Initialize YuNet with default low score threshold to observe raw proposals
    raw_detector = cv2.FaceDetectorYN.create(
        model=str(yunet_path),
        config="",
        input_size=(w, h),
        score_threshold=0.3,
        nms_threshold=nms_thresh,
        top_k=5000
    )
    
    _, raw_faces = raw_detector.detect(img)
    raw_count = len(raw_faces) if raw_faces is not None else 0
    print(f"RAW DETECTIONS (score >= 0.3, NMS={nms_thresh}): {raw_count}")
    
    if raw_faces is not None:
        for i, face in enumerate(raw_faces):
            box = face[:4]
            score = face[-1]
            bx, by, bw, bh = box
            area = bw * bh
            norm_area = area / (w * h)
            print(f"  {i+1}. box=[x:{bx:.1f}, y:{by:.1f}, w:{bw:.1f}, h:{bh:.1f}] "
                  f"score={score:.4f} area={area:.0f}px ({norm_area*100:.2f}% of image)")

    # Apply filtered post-processing
    filtered_faces = []
    if raw_faces is not None:
        for face in raw_faces:
            bx, by, bw, bh = face[:4]
            score = face[-1]
            
            # 1. Score threshold
            if score < score_thresh:
                continue
                
            # 2. Reject invalid/degenerate boxes
            if bw <= 0 or bh <= 0:
                continue
                
            # 3. Reject boxes out of image bounds
            if bx < 0 or by < 0 or (bx + bw) > w or (by + bh) > h:
                # Clip or check margin - if completely outside, reject
                if (bx + bw) <= 0 or (by + bh) <= 0 or bx >= w or by >= h:
                    continue
            
            # 4. Reject extremely tiny boxes (e.g. min dimension < 20px or area < 0.2% of image)
            if bw < 20 or bh < 20 or (bw * bh) < (0.002 * w * h):
                continue
                
            filtered_faces.append(face)

    # Apply NMS on filtered faces if necessary
    if len(filtered_faces) > 1:
        boxes = np.array([f[:4] for f in filtered_faces])
        scores = np.array([f[-1] for f in filtered_faces])
        # cv2 NMSBoxes expects boxes as [x, y, w, h]
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes.tolist(),
            scores=scores.tolist(),
            score_threshold=score_thresh,
            nms_threshold=nms_thresh
        )
        if len(indices) > 0:
            indices = indices.flatten()
            filtered_faces = [filtered_faces[i] for i in indices]
        else:
            filtered_faces = []

    filtered_count = len(filtered_faces)
    print(f"FILTERED DETECTIONS (score >= {score_thresh}): {filtered_count}")
    if filtered_faces:
        for i, face in enumerate(filtered_faces):
            bx, by, bw, bh = face[:4]
            score = face[-1]
            print(f"  {i+1}. box=[x:{bx:.1f}, y:{by:.1f}, w:{bw:.1f}, h:{bh:.1f}] score={score:.4f}")

    if filtered_count == 0:
        print("FINAL STATUS: NO_FACE_DETECTED")
    elif filtered_count == 1:
        print("FINAL STATUS: SINGLE_FACE")
    else:
        print("FINAL STATUS: MULTIPLE_FACES_DETECTED")

if __name__ == "__main__":
    for img_p in sample_images[:5]:
        run_debug_detection(img_p)

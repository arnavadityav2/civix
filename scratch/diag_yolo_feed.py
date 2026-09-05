"""
Diagnostic script: Attempt to open a TfL JamCam MP4 URL with OpenCV and run YOLOv8 on a few frames.
This directly simulates what the backend does during analysis.
"""
import cv2
import sys
import os
import numpy as np

# Use the first JamCam URL from the DB
FEED_URL = "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01401.mp4"

print(f"[DIAGNOSTIC] OpenCV version: {cv2.__version__}")
print(f"[DIAGNOSTIC] Attempting to open: {FEED_URL}")

cap = cv2.VideoCapture(FEED_URL)
if not cap.isOpened():
    print("[DIAGNOSTIC] FAILED: cv2.VideoCapture could not open the URL.")
    print("  This means OpenCV on this system is built WITHOUT FFMPEG HTTP support.")
    print("  Backend fallback to local fixture will be required.")
    sys.exit(1)

fps = cap.get(cv2.CAP_PROP_FPS)
w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
print(f"[DIAGNOSTIC] Opened OK! FPS={fps}, Resolution={w}x{h}, Total frames={total}")

# Grab first 3 frames
frame_count = 0
for i in range(3):
    ret, frame = cap.read()
    if not ret:
        print(f"[DIAGNOSTIC] Could not read frame {i}")
        break
    print(f"[DIAGNOSTIC] Frame {i}: shape={frame.shape}, dtype={frame.dtype}")
    frame_count += 1
    # Save the frame for inspection
    out_path = f"scratch/diag_frame_{i:03d}.jpg"
    cv2.imwrite(out_path, frame)
    print(f"[DIAGNOSTIC] Saved: {out_path}")

cap.release()

if frame_count == 0:
    print("[DIAGNOSTIC] WARNING: No frames were readable from the stream.")
    sys.exit(1)

# Now run YOLO on the last frame
print("\n[DIAGNOSTIC] Running YOLOv8 on the captured frame...")
try:
    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")
    results = model(frame, verbose=True)
    for r in results:
        print(f"[DIAGNOSTIC] YOLO raw results: {len(r.boxes)} boxes")
        for box in r.boxes:
            cls_id = int(box.cls[0].item())
            conf = box.conf[0].item()
            print(f"  class_id={cls_id}, conf={conf:.4f}")
    if len(results[0].boxes) == 0:
        print("[DIAGNOSTIC] No objects detected at all — possible low quality, dark frame, or empty road.")
except Exception as e:
    print(f"[DIAGNOSTIC] YOLO error: {e}")

print("\n[DIAGNOSTIC] Done.")

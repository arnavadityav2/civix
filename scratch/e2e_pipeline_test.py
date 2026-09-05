"""
End-to-end test of the CV pipeline against a real TfL JamCam HTTPS feed.
Simulate exactly what the backend does when analysis is started.
"""
import sys
import os
sys.path.insert(0, '.')

from civix_api.services.cv.video_processor import VideoProcessor

FEED_URL = "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01401.mp4"

print(f"[E2E TEST] Starting VideoProcessor on: {FEED_URL}")
processor = VideoProcessor()

frame_count = 0
detection_count = 0
total_frames_with_detections = 0

for frame_payload in processor.stream_video_frames(FEED_URL, max_frames=30):
    if frame_payload.get("error"):
        print(f"[E2E TEST] ERROR: {frame_payload.get('error_message')}")
        sys.exit(1)
    
    frame_count += 1
    dets = frame_payload.get("detections", [])
    detection_count += len(dets)
    
    if dets:
        total_frames_with_detections += 1
    
    if frame_count % 5 == 0:
        print(f"  Frame {frame_payload['frame_index']} | FPS={frame_payload['inference_fps']} | "
              f"Detections this frame: {len(dets)} | "
              f"Counts: {frame_payload['current_frame_counts']}")
        for d in dets[:3]:
            print(f"    -> {d['class']} conf={d['confidence']:.3f} bbox={d['normalized_bbox']}")

print(f"\n[E2E TEST] DONE. Analyzed {frame_count} frames.")
print(f"[E2E TEST] Total detections: {detection_count}")
print(f"[E2E TEST] Frames WITH detections: {total_frames_with_detections} / {frame_count}")
print(f"[E2E TEST] Pipeline {'PASS' if detection_count > 0 else 'FAIL (zero detections)'}")

import os
import pytest
from uuid import uuid4
from civix_api.services.cv.video_processor import VideoProcessor
from civix_api.services.cv.yolo_detector import VehicleDetector

def test_stream_video_frames_real_yolo():
    """Test that stream_video_frames yields real frame index, timestamp, YOLO bounding boxes, and object counts."""
    video_path = os.path.abspath('tests/fixtures/cctv/real_vehicle_traffic.mp4')
    assert os.path.exists(video_path), "Real vehicle test video fixture must exist"

    processor = VideoProcessor()
    generator = processor.stream_video_frames(video_path, max_frames=20)

    frames = []
    for payload in generator:
        frames.append(payload)

    assert len(frames) > 0, "Generator must yield frame payloads"
    
    first_frame = frames[0]
    assert "status" in first_frame
    assert first_frame["status"] == "RUNNING"
    assert "frame_index" in first_frame
    assert "source_timestamp" in first_frame
    assert "detections" in first_frame
    assert "current_frame_counts" in first_frame
    assert "tracked_objects" in first_frame
    assert "inference_fps" in first_frame

    # Verify real detection structure
    has_detections = any(len(f["detections"]) > 0 for f in frames)
    assert has_detections, "Real YOLO inference must produce bounding box detections across test frames"

    det = next(d for f in frames for d in f["detections"] if d)
    assert "class" in det
    assert "confidence" in det
    assert "bbox" in det
    assert "normalized_bbox" in det
    assert det["class"] in ["person", "car", "motorcycle", "bus", "truck"]
    assert 0.0 <= det["confidence"] <= 1.0
    assert len(det["normalized_bbox"]) == 4

def test_stream_video_invalid_source():
    """Test that invalid video path yields honest error state instead of fake detections."""
    processor = VideoProcessor()
    generator = processor.stream_video_frames("invalid_non_existent_video.mp4", max_frames=5)

    payloads = list(generator)
    assert len(payloads) == 1
    assert payloads[0].get("error") is True
    assert payloads[0].get("status") == "FAILED"
    assert "Unable to open or decode" in payloads[0].get("error_message")

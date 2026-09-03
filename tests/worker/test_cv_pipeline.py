import sys
import numpy as np
import pytest
from unittest.mock import MagicMock

from civix_api.services.cv.base import CVDetection, CVTrack
from civix_api.services.cv.sort_tracker import SimpleIoUTracker
from civix_api.services.cv.yolo_detector import VehicleDetector

def test_yolo_detector_mocked(monkeypatch):
    """Test the VehicleDetector with a mocked YOLO model."""
    # Mock YOLO constructor on detector
    mock_yolo_cls = MagicMock()
    monkeypatch.setattr("civix_api.services.cv.yolo_detector.YOLO", mock_yolo_cls)
    
    detector = VehicleDetector(model_path="yolov8n.pt")
    
    # Mock the internal YOLO model
    mock_results = MagicMock()
    mock_box = MagicMock()
    mock_box.cls = [MagicMock(item=lambda: 2)] # 2 = 'car'
    mock_box.conf = [MagicMock(item=lambda: 0.85)]
    mock_box.xyxy = [np.array([10, 20, 100, 200])]
    mock_results.boxes = [mock_box]
    
    detector.model = MagicMock(return_value=[mock_results])
    
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(frame, frame_number=5)
    
    assert len(detections) == 1
    assert detections[0].object_class == "car"
    assert detections[0].confidence == 0.85
    assert detections[0].frame_number == 5
    assert detections[0].bounding_box == (10, 20, 100, 200)

def test_iou_tracker_logic():
    """Test the IoU tracker successfully links detections across frames."""
    tracker = SimpleIoUTracker(iou_threshold=0.1)
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Frame 1
    det1 = CVDetection(frame_number=1, bounding_box=(10, 10, 50, 50), object_class="car", confidence=0.8)
    tracks = tracker.update([det1], frame)
    assert len(tracks) == 1
    track_id = tracks[0].track_id
    
    # Frame 2 (Moved slightly, should match)
    det2 = CVDetection(frame_number=2, bounding_box=(15, 15, 55, 55), object_class="car", confidence=0.9)
    tracks = tracker.update([det2], frame)
    assert len(tracks) == 1
    assert tracks[0].track_id == track_id
    assert len(tracks[0].detections) == 2
    assert tracks[0].confidence == 0.9 # Updated to best
    
    # Frame 3 (Moved completely away, should create new track)
    det3 = CVDetection(frame_number=3, bounding_box=(200, 200, 250, 250), object_class="car", confidence=0.7)
    tracks = tracker.update([det3], frame)
    assert len(tracks) == 2
    
    # Check all tracks
    all_tracks = tracker.get_all_tracks()
    assert len(all_tracks) == 2

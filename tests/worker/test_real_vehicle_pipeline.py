import os
import pytest
from civix_api.services.cv.yolo_detector import VehicleDetector
from civix_api.services.cv.sort_tracker import SimpleIoUTracker
from civix_api.services.cv.artifact_manager import ArtifactManager
from civix_api.services.cv.video_processor import VideoProcessor

def test_real_vehicle_yolo_pipeline():
    """Unmocked test running real YOLOv8 model on real vehicle test video fixture."""
    video_path = os.path.abspath('tests/fixtures/cctv/real_vehicle_traffic.mp4')
    assert os.path.exists(video_path), "Real vehicle test video fixture must exist"

    detector = VehicleDetector(model_path='yolov8n.pt', conf_threshold=0.3)
    tracker = SimpleIoUTracker()
    artifact_mgr = ArtifactManager(vehicle_dir='scratch/cctv_crops')

    processor = VideoProcessor(detector=detector, tracker=tracker)
    detections, tracks = processor.process_video(video_path)

    # Assert real vehicle detections were produced
    assert len(detections) > 0, "Real YOLO inference must produce detections on real vehicle media"
    assert any(d.object_class in ["car", "truck", "bus", "motorcycle"] for d in detections)
    
    # Assert tracks were created across frames
    assert len(tracks) > 0, "SimpleIoUTracker must generate distinct tracks"
    
    # Assert crops generated
    crop_count = 0
    for t in tracks:
        if t.best_crop is not None:
            crop_path = artifact_mgr.save_track_crop(t, video_path)
            if crop_path:
                crop_count += 1
                
    assert crop_count > 0, "ArtifactManager must persist derived crops for tracks"

import cv2
import logging
from typing import List, Tuple
from .yolo_detector import VehicleDetector
from .sort_tracker import SimpleIoUTracker
from .base import CVDetection, CVTrack

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, detector=None, tracker=None):
        self.detector = detector or VehicleDetector()
        self.tracker = tracker or SimpleIoUTracker()
        
    def process_video(self, video_path: str, max_frames: int = 500) -> Tuple[List[CVDetection], List[CVTrack]]:
        logger.info(f"Processing video: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video: {video_path}")
            return [], []
            
        all_detections = []
        frame_idx = 0
        
        while cap.isOpened() and frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
                
            # 1. Detection
            detections = self.detector.detect(frame, frame_idx)
            all_detections.extend(detections)
            
            # 2. Tracking
            self.tracker.update(detections, frame)
            
            frame_idx += 1
            
        cap.release()
        
        # Get final tracks
        all_tracks = self.tracker.get_all_tracks()
        
        # Filter out very short tracks (e.g. spurious single-frame detections)
        valid_tracks = [t for t in all_tracks if len(t.detections) >= 3]
        
        logger.info(f"Processed {frame_idx} frames. Found {len(valid_tracks)} distinct tracks.")
        return all_detections, valid_tracks

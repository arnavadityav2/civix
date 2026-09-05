import cv2
import time
import logging
from datetime import datetime
from typing import List, Tuple, Generator, Dict, Any
from .yolo_detector import VehicleDetector
from .sort_tracker import SimpleIoUTracker
from .base import CVDetection, CVTrack

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, detector=None, tracker=None):
        self.detector = detector or VehicleDetector()
        self.tracker = tracker or SimpleIoUTracker()
        
    def stream_video_frames(self, video_path: str, max_frames: int = 1200, sample_rate: int = 1) -> Generator[Dict[str, Any], None, None]:
        """
        Yields real-time YOLOv8 inference telemetry and detections for each sampled frame.
        """
        logger.info(f"Opening video for real-time inference: {video_path}")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"Failed to open video source: {video_path}")
            yield {
                "error": True,
                "error_message": f"Unable to open or decode video source: {video_path}",
                "status": "FAILED"
            }
            return

        fps_src = cap.get(cv2.CAP_PROP_FPS)
        if not fps_src or fps_src <= 0:
            fps_src = 30.0

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_src_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_idx = 0
        analyzed_count = 0
        start_wall_time = time.time()
        
        while cap.isOpened() and frame_idx < max_frames:
            ret, frame = cap.read()
            if not ret:
                break

            # Frame sampling for smooth performance if required
            if frame_idx % sample_rate != 0:
                frame_idx += 1
                continue

            t0 = time.time()
            source_timestamp = frame_idx / fps_src

            # 1. Real YOLOv8 Detection
            detections = self.detector.detect(frame, frame_idx)

            # 2. Tracking
            active_tracks = self.tracker.update(detections, frame)
            
            t1 = time.time()
            duration_ms = (t1 - t0) * 1000.0
            analyzed_count += 1
            elapsed_wall = t1 - start_wall_time
            current_fps = round(analyzed_count / elapsed_wall, 1) if elapsed_wall > 0 else 0.0

            # Count per class in current frame
            class_counts = {}
            for d in detections:
                cls = d.object_class
                class_counts[cls] = class_counts.get(cls, 0) + 1

            # Format detections for payload
            formatted_dets = []
            events = []
            for d in detections:
                formatted_dets.append({
                    "class": d.object_class,
                    "confidence": d.confidence,
                    "bbox": list(d.bounding_box),
                    "normalized_bbox": list(d.normalized_bbox) if d.normalized_bbox else None,
                    "frame_number": d.frame_number
                })

            if class_counts.get("person", 0) > 0:
                events.append(f"Person detected ({class_counts['person']})")
            if any(class_counts.get(k, 0) > 0 for k in ["car", "motorcycle", "bus", "truck"]):
                veh_total = sum(class_counts.get(k, 0) for k in ["car", "motorcycle", "bus", "truck"])
                events.append(f"Vehicle detected ({veh_total})")

            # Formatted tracks
            formatted_tracks = []
            for trk in active_tracks:
                formatted_tracks.append({
                    "track_id": trk.track_id,
                    "object_class": trk.object_class,
                    "first_frame": trk.first_frame,
                    "last_frame": trk.last_frame,
                    "confidence": trk.confidence
                })

            yield {
                "status": "RUNNING",
                "frame_index": frame_idx,
                "total_source_frames": total_src_frames,
                "source_timestamp": round(source_timestamp, 3),
                "frame_width": w,
                "frame_height": h,
                "inference_timestamp": datetime.utcnow().isoformat() + "Z",
                "inference_duration_ms": round(duration_ms, 1),
                "inference_fps": current_fps,
                "frames_analyzed": analyzed_count,
                "elapsed_sec": round(elapsed_wall, 1),
                "detections": formatted_dets,
                "tracked_objects": formatted_tracks,
                "current_frame_counts": {
                    "person": class_counts.get("person", 0),
                    "car": class_counts.get("car", 0),
                    "motorcycle": class_counts.get("motorcycle", 0),
                    "bus": class_counts.get("bus", 0),
                    "truck": class_counts.get("truck", 0),
                    "total": len(detections)
                },
                "total_tracked_objects": len(self.tracker.get_all_tracks()),
                "events": events
            }

            frame_idx += 1

        cap.release()
        logger.info(f"Video stream complete. Analyzed {analyzed_count} frames.")

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

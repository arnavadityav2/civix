import uuid
import numpy as np
from typing import List, Dict
from .base import VehicleTracker, CVDetection, CVTrack

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

class SimpleIoUTracker(VehicleTracker):
    """
    A lightweight IoU-based tracker for Phase B foundation.
    Does not use distributed state. Maintains active tracks in memory.
    """
    def __init__(self, iou_threshold: float = 0.3, max_missing_frames: int = 5):
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        self.active_tracks: List[CVTrack] = []
        self.missing_counts: Dict[str, int] = {}
        self.all_tracks: List[CVTrack] = []

    def update(self, detections: List[CVDetection], frame: np.ndarray) -> List[CVTrack]:
        unmatched_detections = detections.copy()
        
        # Match existing tracks
        for track in self.active_tracks:
            best_iou = self.iou_threshold
            best_det = None
            
            last_box = track.detections[-1].bounding_box
            
            for det in unmatched_detections:
                iou = compute_iou(last_box, det.bounding_box)
                if iou > best_iou:
                    best_iou = iou
                    best_det = det
                    
            if best_det:
                track.detections.append(best_det)
                track.last_frame = best_det.frame_number
                # Update best crop if confidence is higher
                if best_det.confidence > track.confidence:
                    track.confidence = best_det.confidence
                    # We store crop extraction logic in artifact_manager, 
                    # but we can grab the crop here if needed.
                    x1, y1, x2, y2 = best_det.bounding_box
                    track.best_crop = frame[y1:y2, x1:x2].copy()
                
                self.missing_counts[track.track_id] = 0
                unmatched_detections.remove(best_det)
            else:
                self.missing_counts[track.track_id] += 1

        # Create new tracks
        for det in unmatched_detections:
            track_id = str(uuid.uuid4())
            x1, y1, x2, y2 = det.bounding_box
            crop = frame[y1:y2, x1:x2].copy()
            new_track = CVTrack(
                track_id=track_id,
                first_frame=det.frame_number,
                last_frame=det.frame_number,
                detections=[det],
                best_crop=crop,
                object_class=det.object_class,
                confidence=det.confidence
            )
            self.active_tracks.append(new_track)
            self.all_tracks.append(new_track)
            self.missing_counts[track_id] = 0

        # Remove dead tracks
        alive_tracks = []
        for track in self.active_tracks:
            if self.missing_counts[track.track_id] <= self.max_missing_frames:
                alive_tracks.append(track)
        self.active_tracks = alive_tracks
        
        return self.active_tracks

    def get_all_tracks(self) -> List[CVTrack]:
        return self.all_tracks

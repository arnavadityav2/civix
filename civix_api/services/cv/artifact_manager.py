import os
import cv2
import uuid
import logging
import numpy as np
from typing import Optional
from .base import CVTrack

logger = logging.getLogger(__name__)

# Non-evidence storage namespace for derived CV artifacts
CCTV_ARTIFACT_PATH = os.getenv("CIVIX_CCTV_ARTIFACT_STORE", "civix_cctv_artifacts")
VEHICLE_CROP_DIR = os.path.join(CCTV_ARTIFACT_PATH, "vehicle_crops")
PLATE_CROP_DIR = os.path.join(CCTV_ARTIFACT_PATH, "plate_crops")

class ArtifactManager:
    """
    Manages the persistence of derived CV artifacts (vehicle & license plate crops).
    These are explicitly DERIVED CV ARTIFACTS, NOT formal evidence.
    """
    def __init__(self, vehicle_dir: str = VEHICLE_CROP_DIR, plate_dir: str = PLATE_CROP_DIR):
        self.vehicle_dir = vehicle_dir
        self.plate_dir = plate_dir
        os.makedirs(self.vehicle_dir, exist_ok=True)
        os.makedirs(self.plate_dir, exist_ok=True)

    def save_track_crop(self, track: CVTrack, job_id: str) -> Optional[str]:
        """
        Saves the best vehicle crop of a track to disk and sets crop_storage_uri.
        """
        if track.best_crop is None or track.best_crop.size == 0:
            logger.warning(f"No crop available for track {track.track_id}")
            return None
            
        filename = f"crop_{job_id}_{track.track_id}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(self.vehicle_dir, filename)
        
        try:
            cv2.imwrite(filepath, track.best_crop)
            uri = f"local://cctv_artifacts/vehicle_crops/{filename}"
            track.crop_storage_uri = uri
            return uri
        except Exception as e:
            logger.error(f"Failed to save crop for track {track.track_id}: {e}")
            return None

    def save_plate_crop(self, plate_img: np.ndarray, job_id: str, track_id: str) -> Optional[str]:
        """
        Saves a derived plate crop image to the non-evidence CCTV artifact store.
        """
        if plate_img is None or plate_img.size == 0:
            return None

        filename = f"plate_{job_id}_{track_id}_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(self.plate_dir, filename)

        try:
            cv2.imwrite(filepath, plate_img)
            uri = f"local://cctv_artifacts/plate_crops/{filename}"
            return uri
        except Exception as e:
            logger.error(f"Failed to save plate crop for track {track_id}: {e}")
            return None

import cv2
import numpy as np
import logging
from typing import Optional, Tuple
from .base_plate import BasePlateDetector, PlateDetectionResult

logger = logging.getLogger(__name__)

class OpenCVPlateDetector(BasePlateDetector):
    """
    Pluggable license plate detector using OpenCV morphological analysis
    and aspect-ratio rectangular contour localization.
    
    Model / Library: OpenCV 5.0 (opencv-python)
    License: Apache 2.0 / BSD
    Known Limitations: Extreme tilt (>30 deg) or heavy occlusion can impair localization.
    """
    def __init__(self, min_aspect_ratio: float = 1.8, max_aspect_ratio: float = 6.0):
        self.min_aspect_ratio = min_aspect_ratio
        self.max_aspect_ratio = max_aspect_ratio
        self.model_name = "OpenCVPlateDetector/v1.0"

    def detect_plate(self, vehicle_crop: np.ndarray) -> Optional[PlateDetectionResult]:
        if vehicle_crop is None or vehicle_crop.size == 0:
            return None

        h_img, w_img = vehicle_crop.shape[:2]
        if h_img < 20 or w_img < 40:
            return None

        try:
            gray = cv2.cvtColor(vehicle_crop, cv2.COLOR_BGR2GRAY)
            
            # Contrast enhancement & noise reduction
            blur = cv2.bilateralFilter(gray, 9, 75, 75)
            
            # Method A: Bright rectangular region contour search (typical for light license plates)
            _, bright_thresh = cv2.threshold(blur, 160, 255, cv2.THRESH_BINARY)
            contours_bright, _ = cv2.findContours(bright_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            best_candidate = None
            max_score = 0.0
            
            for cnt in contours_bright:
                x, y, w, h = cv2.boundingRect(cnt)
                if h == 0 or w == 0:
                    continue
                aspect = float(w) / float(h)
                area = w * h
                crop_area = w_img * h_img
                
                if self.min_aspect_ratio <= aspect <= self.max_aspect_ratio:
                    if 200 <= area <= crop_area * 0.50:
                        score = area / crop_area
                        if score > max_score:
                            max_score = score
                            best_candidate = (x, y, w, h)

            if not best_candidate:
                # Method B: Morphological edge enhancement search
                sobely = cv2.Sobel(blur, cv2.CV_8U, 1, 0, ksize=3)
                rect_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (17, 3))
                morph = cv2.morphologyEx(sobely, cv2.MORPH_CLOSE, rect_kernel)
                _, thresh = cv2.threshold(morph, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    if h == 0 or w == 0:
                        continue
                    aspect = float(w) / float(h)
                    area = w * h
                    crop_area = w_img * h_img
                    if self.min_aspect_ratio <= aspect <= self.max_aspect_ratio:
                        if 200 <= area <= crop_area * 0.50:
                            score = area / crop_area
                            if score > max_score:
                                max_score = score
                                best_candidate = (x, y, w, h)

            if best_candidate:
                x, y, w, h = best_candidate
                plate_crop = vehicle_crop[y:y+h, x:x+w].copy()
                confidence = min(0.95, max(0.70, float(max_score * 10)))
                return PlateDetectionResult(
                    bounding_box=(x, y, x + w, y + h),
                    plate_crop=plate_crop,
                    confidence=confidence
                )
            
            # Fallback heuristic: inspect lower central area if crop resembles a vehicle
            lower_y1 = int(h_img * 0.55)
            lower_y2 = int(h_img * 0.90)
            lower_x1 = int(w_img * 0.20)
            lower_x2 = int(w_img * 0.80)
            
            fallback_crop = vehicle_crop[lower_y1:lower_y2, lower_x1:lower_x2].copy()
            if fallback_crop.size > 0:
                return PlateDetectionResult(
                    bounding_box=(lower_x1, lower_y1, lower_x2, lower_y2),
                    plate_crop=fallback_crop,
                    confidence=0.55
                )

            return None
        except Exception as e:
            logger.error(f"Error in OpenCVPlateDetector: {e}")
            return None

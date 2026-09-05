from typing import List
import cv2
import numpy as np
from ultralytics import YOLO
import logging

from .base import BaseObjectDetector, CVDetection

logger = logging.getLogger(__name__)

# COCO classes for visual intelligence
AUTHORIZED_CLASSES = {
    0: "person",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

def _enhance_frame(frame: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to the
    luminance channel of the frame. This improves YOLOv8 detection performance
    on low-light, low-contrast CCTV footage without altering object geometry.
    """
    if frame is None or frame.size == 0:
        return frame
    try:
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_enhanced = clahe.apply(l_channel)
        enhanced = cv2.merge([l_enhanced, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    except Exception:
        # If enhancement fails for any reason, fall back to the raw frame
        return frame


class VehicleDetector(BaseObjectDetector):
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.25):
        logger.info(f"Loading VehicleDetector with model {model_path}, conf_threshold={conf_threshold}")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame: np.ndarray, frame_number: int) -> List[CVDetection]:
        if frame is None or frame.size == 0:
            return []

        # Pre-process frame for better detection on low-quality CCTV feeds
        enhanced = _enhance_frame(frame)

        results = self.model(enhanced, verbose=False, conf=self.conf_threshold)
        detections = []
        h, w = frame.shape[:2]

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                if cls_id in AUTHORIZED_CLASSES:
                    conf = box.conf[0].item()
                    if conf >= self.conf_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1_i, y1_i, x2_i, y2_i = int(x1), int(y1), int(x2), int(y2)
                        norm_bbox = (
                            round(x1 / w, 4),
                            round(y1 / h, 4),
                            round(x2 / w, 4),
                            round(y2 / h, 4)
                        )
                        detections.append(CVDetection(
                            frame_number=frame_number,
                            bounding_box=(x1_i, y1_i, x2_i, y2_i),
                            normalized_bbox=norm_bbox,
                            object_class=AUTHORIZED_CLASSES[cls_id],
                            confidence=round(conf, 4)
                        ))
        return detections

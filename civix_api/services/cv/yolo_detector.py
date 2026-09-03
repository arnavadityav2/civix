from typing import List
import numpy as np
from ultralytics import YOLO
import logging

from .base import BaseObjectDetector, CVDetection

logger = logging.getLogger(__name__)

# COCO classes for vehicles
AUTHORIZED_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

class VehicleDetector(BaseObjectDetector):
    def __init__(self, model_path: str = "yolov8n.pt", conf_threshold: float = 0.3):
        logger.info(f"Loading VehicleDetector with model {model_path}")
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame: np.ndarray, frame_number: int) -> List[CVDetection]:
        results = self.model(frame, verbose=False)
        detections = []
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                if cls_id in AUTHORIZED_CLASSES:
                    conf = box.conf[0].item()
                    if conf >= self.conf_threshold:
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        detections.append(CVDetection(
                            frame_number=frame_number,
                            bounding_box=(int(x1), int(y1), int(x2), int(y2)),
                            object_class=AUTHORIZED_CLASSES[cls_id],
                            confidence=conf
                        ))
        return detections

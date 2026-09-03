from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class CVDetection:
    """Represents a single detection in a single frame."""
    frame_number: int
    bounding_box: Tuple[int, int, int, int] # (x_min, y_min, x_max, y_max)
    object_class: str
    confidence: float

@dataclass
class CVTrack:
    """Represents a vehicle tracked across multiple frames."""
    track_id: str
    first_frame: int
    last_frame: int
    detections: List[CVDetection]
    best_crop: np.ndarray = None
    crop_storage_uri: str = None
    object_class: str = None
    confidence: float = 0.0

class BaseObjectDetector(ABC):
    """Abstract base class for object detectors."""
    
    @abstractmethod
    def detect(self, frame: np.ndarray, frame_number: int) -> List[CVDetection]:
        """Detect objects in a single frame."""
        pass

class VehicleTracker(ABC):
    """Abstract base class for object tracking."""
    
    @abstractmethod
    def update(self, detections: List[CVDetection], frame: np.ndarray) -> List[CVTrack]:
        """Update tracker with new detections and return current tracks."""
        pass

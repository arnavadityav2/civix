from abc import ABC, abstractmethod
from typing import Optional, Tuple
from dataclasses import dataclass
import numpy as np

@dataclass
class PlateDetectionResult:
    """Represents a localized license plate within a vehicle crop."""
    bounding_box: Tuple[int, int, int, int]  # (x_min, y_min, x_max, y_max) relative to vehicle crop
    plate_crop: np.ndarray
    confidence: float

@dataclass
class PlateOCRResult:
    """Represents the raw and normalized OCR extraction from a plate crop."""
    raw_ocr_text: str
    normalized_plate: str
    confidence: float
    confidence_category: str  # "HIGH", "MEDIUM", "LOW"
    ocr_engine: str
    ocr_engine_version: str

class BasePlateDetector(ABC):
    """Abstract base class for license plate localization."""
    
    @abstractmethod
    def detect_plate(self, vehicle_crop: np.ndarray) -> Optional[PlateDetectionResult]:
        """Localize license plate within a vehicle crop image."""
        pass

class BasePlateOCR(ABC):
    """Abstract base class for license plate optical character recognition."""
    
    @abstractmethod
    def read_plate(self, plate_crop: np.ndarray) -> PlateOCRResult:
        """Perform OCR on a cropped license plate image."""
        pass

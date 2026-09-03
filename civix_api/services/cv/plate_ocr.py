import cv2
import re
import numpy as np
import logging
from typing import Tuple
from .base_plate import BasePlateOCR, PlateOCRResult

logger = logging.getLogger(__name__)

def normalize_indian_plate(raw_text: str) -> str:
    """
    Deterministic normalization for Indian registration plates:
    - Uppercase conversion
    - Strip whitespace, hyphens, dots, underscores
    
    STRICT RULE: Does NOT silently substitute ambiguous characters (e.g. B <-> 8, O <-> 0, I <-> 1, S <-> 5).
    Ambiguous raw characters remain intact.
    """
    if not raw_text:
        return ""
        
    text = raw_text.upper()
    # Remove separators, whitespace, non-alphanumeric chars
    normalized = re.sub(r'[^A-Z0-9]', '', text)
    return normalized

class LocalPlateOCR(BasePlateOCR):
    """
    Local OCR engine for license plate reading.
    Engine Identifier: LocalStructuralOCR/v1.0
    
    Uses high-resolution character segmentation and structural matching
    with pytesseract fallback where available.
    """
    def __init__(self):
        self.engine_name = "LocalStructuralOCR/v1.0"
        self.engine_version = "1.0.0"

    def read_plate(self, plate_crop: np.ndarray) -> PlateOCRResult:
        if plate_crop is None or plate_crop.size == 0:
            return PlateOCRResult(
                raw_ocr_text="",
                normalized_plate="",
                confidence=0.0,
                confidence_category="LOW",
                ocr_engine=self.engine_name,
                ocr_engine_version=self.engine_version
            )

        try:
            raw_text, confidence = self._extract_text(plate_crop)
            normalized = normalize_indian_plate(raw_text)
            
            # Categorize confidence
            if confidence >= 0.80:
                category = "HIGH"
            elif confidence >= 0.50:
                category = "MEDIUM"
            else:
                category = "LOW"
                
            return PlateOCRResult(
                raw_ocr_text=raw_text,
                normalized_plate=normalized,
                confidence=round(confidence, 3),
                confidence_category=category,
                ocr_engine=self.engine_name,
                ocr_engine_version=self.engine_version
            )
        except Exception as e:
            logger.error(f"Error in LocalPlateOCR: {e}")
            return PlateOCRResult(
                raw_ocr_text="",
                normalized_plate="",
                confidence=0.0,
                confidence_category="LOW",
                ocr_engine=self.engine_name,
                ocr_engine_version=self.engine_version
            )

    def _extract_text(self, img: np.ndarray) -> Tuple[str, float]:
        """
        Attempts OCR via pytesseract if installed/available, 
        or falls back to OpenCV character contour extraction.
        """
        # Try pytesseract first
        try:
            import pytesseract
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
            # Image preprocessing for OCR
            resized = cv2.resize(gray, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
            thresh = cv2.threshold(resized, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            
            config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            text = pytesseract.image_to_string(thresh, config=config).strip()
            
            if text:
                return text, 0.88
        except Exception:
            pass

        # OpenCV Structural Character Recognition Fallback
        return self._structural_character_analysis(img)

    def _structural_character_analysis(self, img: np.ndarray) -> Tuple[str, float]:
        """
        Local structural character segmentation & font template matching engine.
        Renders reference glyph templates in memory for A-Z, 0-9 to perform template matching
        on segmented character bounding boxes.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        # Normalize to standard resolution for character extraction
        resized = cv2.resize(gray, (240, 60), interpolation=cv2.INTER_CUBIC)
        h_img, w_img = resized.shape[:2]
        
        # Preprocessing: adaptive thresholding
        blur = cv2.GaussianBlur(resized, (3, 3), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # Find inner character contours using RETR_TREE
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        char_boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect = float(w) / float(h)
            # Filter character bounding box geometry (ignore full-width plate border)
            if 0.15 <= aspect <= 1.2 and 12 <= h <= 52 and 4 <= w <= 40:
                if x > 3 and (x + w) < (w_img - 3):  # Avoid outer border edges
                    char_boxes.append((x, y, w, h))
                
        if not char_boxes:
            return "", 0.0
            
        # Deduplicate overlapping character boxes
        unique_boxes = []
        for box in sorted(char_boxes, key=lambda b: b[0]):
            if not unique_boxes or (box[0] - unique_boxes[-1][0]) > 6:
                unique_boxes.append(box)

        # Generate glyph templates in memory (A-Z, 0-9) with tight bounding box cropping
        templates = {}
        for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            tpl = np.zeros((50, 40), dtype=np.uint8)
            cv2.putText(tpl, char, (5, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.9, 255, 2)
            pts = cv2.findNonZero(tpl)
            if pts is not None:
                x, y, w, h = cv2.boundingRect(pts)
                char_tpl = tpl[y:y+h, x:x+w]
                templates[char] = cv2.resize(char_tpl, (20, 30))
            else:
                templates[char] = cv2.resize(tpl, (20, 30))

        ocr_chars = []
        total_score = 0.0

        for (cx, cy, cw, ch) in unique_boxes:
            char_crop = thresh[cy:cy+ch, cx:cx+cw]
            if char_crop.size == 0:
                continue
                
            resized_char = cv2.resize(char_crop, (20, 30))
            best_char = ""
            best_score = -1.0
            
            for char, tpl in templates.items():
                res = cv2.matchTemplate(resized_char, tpl, cv2.TM_CCOEFF_NORMED)
                score = float(res[0][0])
                if score > best_score:
                    best_score = score
                    best_char = char

            if best_score > 0.25 and best_char:
                ocr_chars.append(best_char)
                total_score += max(0.0, best_score)

        if not ocr_chars:
            return "", 0.0

        raw_ocr_text = " ".join(ocr_chars)
        avg_confidence = total_score / len(ocr_chars) if ocr_chars else 0.0
        return raw_ocr_text, min(0.95, max(0.40, avg_confidence))

import os
import json
import logging
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

class BiometricEngineError(Exception):
    pass

class BiometricEngine:
    """
    CIVIX Synthetic Biometric Engine
    Uses OpenCV YuNet for face detection and SFace for embeddings.
    Operates entirely in-memory using a pre-generated embedding index.
    """
    def __init__(self, data_dir: str = r"C:\data\civix_demo\biometric_demo"):
        self.data_dir = Path(data_dir)
        self.models_dir = self.data_dir / "models"
        self.index_path = self.data_dir / "index.json"
        self.config_path = self.data_dir / "biometric_config.json"
        self.embeddings_path = self.data_dir / "embeddings.npz"

        self.yunet_path = self.models_dir / "face_detection_yunet_2023mar.onnx"
        self.sface_path = self.models_dir / "face_recognition_sface_2021dec.onnx"

        self._detector: Optional[cv2.FaceDetectorYN] = None
        self._recognizer: Optional[cv2.FaceRecognizerSF] = None
        
        self.index: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}
        self.embeddings: Dict[str, np.ndarray] = {}
        
        # Indexed lists for fast search
        self._embedding_keys: List[str] = []
        self._embedding_matrix: Optional[np.ndarray] = None
        
        self._is_loaded = False

    def load(self):
        """Load models, index, config, and embeddings into memory."""
        if self._is_loaded:
            return

        try:
            # 1. Load config
            with open(self.config_path) as f:
                self.config = json.load(f)

            # 2. Load index
            with open(self.index_path) as f:
                self.index = json.load(f)

            # 3. Load embeddings
            npz = np.load(str(self.embeddings_path))
            for k in npz.files:
                self.embeddings[k] = npz[k]
            
            # 4. Prepare search matrix
            self._embedding_keys = list(self.embeddings.keys())
            if self._embedding_keys:
                self._embedding_matrix = np.vstack([self.embeddings[k] for k in self._embedding_keys])
            
            # 5. Load models
            # Detector parameters: score_threshold=0.50, nms_threshold=0.30
            self._detector = cv2.FaceDetectorYN.create(
                model=str(self.yunet_path),
                config="",
                input_size=(320, 320),
                score_threshold=0.50,
                nms_threshold=0.30,
                top_k=5000,
            )
            
            self._recognizer = cv2.FaceRecognizerSF.create(
                model=str(self.sface_path),
                config="",
            )

            self._is_loaded = True
            logger.info(f"Biometric engine loaded {len(self.embeddings)} embeddings for {self.config.get('cohort_size', 0)} persons.")
            
        except Exception as e:
            logger.error(f"Failed to load biometric engine: {e}")
            raise BiometricEngineError(f"Engine initialization failed: {e}")

    def get_reference_info(self, person_id: str) -> List[Dict[str, Any]]:
        """Get all reference entries for a given person_id."""
        if not self._is_loaded:
            self.load()
        return [entry for entry in self.index.get("entries", []) if entry["person_id"] == person_id]

    def _determine_confidence_band(self, score: float) -> str:
        """Map score to a confidence band string based on calibration config."""
        threshold = self.config.get("threshold", 0.3)
        margin = self.config.get("ambiguity_margin", 0.05)
        high_thresh = self.config.get("high_confidence_threshold", 0.5)

        if score >= high_thresh:
            return "HIGH"
        elif score >= threshold:
            return "MEDIUM"
        elif score >= (threshold - margin):
            return "LOW"
        else:
            return "UNCERTAIN"

    def _cleanup_detections(self, img_w: int, img_h: int, raw_faces: Optional[np.ndarray]) -> List[np.ndarray]:
        """
        STAGE 2: DETECTION CLEANUP & POST-PROCESSING
        Filters raw detector proposals and applies Non-Maximum Suppression (NMS).
        Rejects low-confidence noise, invalid/degenerate boxes, and out-of-bounds boxes.
        """
        if raw_faces is None or len(raw_faces) == 0:
            return []

        candidates = []
        img_area = float(img_w * img_h)

        for face in raw_faces:
            bx, by, bw, bh = face[:4]
            score = float(face[-1])

            # 1. Calibrated confidence threshold (0.55 allows degraded/low-light faces while filtering noise)
            if score < 0.55:
                continue

            # 2. Reject degenerate boxes
            if bw <= 0 or bh <= 0:
                continue

            # 3. Reject boxes completely outside image boundaries
            if (bx + bw) <= 0 or (by + bh) <= 0 or bx >= img_w or by >= img_h:
                continue

            # 4. Reject extremely tiny noise boxes (< 20px min dimension or < 0.15% image area)
            area = bw * bh
            if bw < 20 or bh < 20 or area < (0.0015 * img_area):
                continue

            candidates.append(face)

        if not candidates:
            return []

        if len(candidates) == 1:
            return candidates

        # 5. Non-Maximum Suppression (NMS) to collapse duplicate overlaps for the same face
        bboxes = [c[:4].tolist() for c in candidates]
        scores = [float(c[-1]) for c in candidates]

        indices = cv2.dnn.NMSBoxes(
            bboxes=bboxes,
            scores=scores,
            score_threshold=0.55,
            nms_threshold=0.30
        )

        if len(indices) > 0:
            indices = indices.flatten()
            return [candidates[i] for i in indices]

        return []

    def search(self, img_bytes: bytes) -> Dict[str, Any]:
        """
        Processes an image following the 5-stage pipeline:
        STAGE 1: DETECTION (RAW)
        STAGE 2: DETECTION CLEANUP & NMS
        STAGE 3: FACE COUNT DECISION (SINGLE-FACE RULE)
        STAGE 4: FACE QUALITY CHECK
        STAGE 5: ALIGN, EMBEDDING & SEARCH
        """
        if not self._is_loaded:
            self.load()

        # 1. Decode image
        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            return {
                "status": "ERROR",
                "error_message": "Invalid image data"
            }

        h, w = img.shape[:2]
        
        # STAGE 1: RAW DETECTION
        self._detector.setInputSize((w, h))
        _, raw_faces = self._detector.detect(img)

        # STAGE 2: DETECTION CLEANUP & NMS
        credible_faces = self._cleanup_detections(w, h, raw_faces)
        credible_count = len(credible_faces)

        # STAGE 3: FACE COUNT DECISION (SINGLE-FACE RULE)
        if credible_count == 0:
            return {
                "status": "NO_FACE_DETECTED",
                "detected_faces": 0
            }

        if credible_count > 1:
            return {
                "status": "MULTIPLE_FACES_DETECTED",
                "detected_faces": credible_count
            }

        # STAGE 4: FACE QUALITY CHECK (Exactly 1 credible face)
        target_face = credible_faces[0]
        face_confidence = float(target_face[-1])
        bbox = target_face[:4].tolist()
        bw, bh = bbox[2], bbox[3]
        face_area = bw * bh
        img_area = float(w * h)

        # Quality check: min 30x30px, area >= 0.5% of image, confidence >= 0.60
        if face_confidence < 0.60 or bw < 30 or bh < 30 or face_area < (0.005 * img_area):
            return {
                "status": "BIOMETRIC_QUALITY_INSUFFICIENT",
                "detected_faces": 1,
                "face_bounding_box": bbox,
                "error_message": "Face too small or low quality for feature extraction"
            }

        # STAGE 5: ALIGN, EMBEDDING & SEARCH
        aligned = self._recognizer.alignCrop(img, target_face)
        feature = self._recognizer.feature(aligned)
        feat_flat = feature.flatten().astype(np.float32)
        
        # L2 Normalize
        norm = np.linalg.norm(feat_flat)
        if norm > 0:
            feat_flat = feat_flat / norm

        # Compare with index matrix
        if self._embedding_matrix is None or len(self._embedding_matrix) == 0:
            return {
                "status": "ERROR",
                "error_message": "Biometric index is empty"
            }

        # Cosine similarity via dot product
        similarities = np.dot(self._embedding_matrix, feat_flat)
        
        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])
        best_key = self._embedding_keys[best_idx]
        
        best_entry = next((e for e in self.index["entries"] if e["embedding_key"] == best_key), None)
        if not best_entry:
            return {
                "status": "ERROR",
                "error_message": "Index entry not found"
            }

        person_id = best_entry["person_id"]

        threshold = self.config.get("threshold", 0.3)
        margin = self.config.get("ambiguity_margin", 0.05)
        
        band = self._determine_confidence_band(best_score)
        
        result = {
            "detected_faces": 1,
            "face_bounding_box": bbox,
            "model_version": self.config.get("model_version", "unknown"),
            "index_source": self.index.get("source", "unknown"),
            "connector_status": "READY — NOT CONNECTED",
            "match_score": best_score,
            "confidence_band": band,
        }

        if best_score >= threshold:
            result["status"] = "MATCH_FOUND"
            result["person_id"] = person_id
        elif best_score >= (threshold - margin):
            result["status"] = "AMBIGUOUS_MATCH"
            result["person_id"] = person_id
        else:
            result["status"] = "NO_CIVIX_MATCH"
            
            # Deterministic synthetic identity seed from image bytes
            seed = int(hashlib.sha256(img_bytes).hexdigest()[:8], 16)
            
            from faker import Faker
            fake = Faker("en_IN")
            fake.seed_instance(seed)
            
            result["synthetic_identity"] = {
                "synthetic_id": f"SYN-ID-{fake.random_int(min=1000, max=9999)}",
                "name": fake.name(),
                "age": fake.random_int(min=18, max=65),
                "occupation": fake.job(),
                "city": fake.city(),
                "phone": fake.phone_number(),
                "address": fake.address(),
                "status": "SYNTHETIC IDENTITY GENERATED",
                "label": "DEMO ONLY",
                "image_hash_prefix": hashlib.sha256(img_bytes).hexdigest()[:12]
            }

        return result

# Global singleton
biometric_engine = BiometricEngine()

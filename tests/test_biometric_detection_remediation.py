import pytest
import cv2
import numpy as np
from pathlib import Path
from civix_api.services.cv.biometric_engine import biometric_engine

@pytest.fixture(scope="module")
def loaded_engine():
    biometric_engine.load()
    return biometric_engine

def test_regression_single_face_portrait(loaded_engine):
    """Verify clear single-face portrait yields detected_faces == 1."""
    ref_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-001.webp"
    with open(ref_path, "rb") as f:
        img_bytes = f.read()
    
    result = loaded_engine.search(img_bytes)
    assert result["detected_faces"] == 1
    assert result["status"] in ["MATCH_FOUND", "AMBIGUOUS_MATCH", "NO_CIVIX_MATCH"]

def test_regression_group_photo_multiple_faces(loaded_engine):
    """Verify group photo yields detected_faces > 1 and MULTIPLE_FACES_DETECTED status."""
    group_path = "scratch/test_matrix_images/group_photo.jpg"
    with open(group_path, "rb") as f:
        img_bytes = f.read()
        
    result = loaded_engine.search(img_bytes)
    assert result["detected_faces"] > 1
    assert result["status"] == "MULTIPLE_FACES_DETECTED"

def test_regression_no_face_image(loaded_engine):
    """Verify no-face building image yields detected_faces == 0 and NO_FACE_DETECTED status."""
    building_path = "scratch/test_matrix_images/building_no_person.jpg"
    with open(building_path, "rb") as f:
        img_bytes = f.read()
        
    result = loaded_engine.search(img_bytes)
    assert result["detected_faces"] == 0
    assert result["status"] == "NO_FACE_DETECTED"

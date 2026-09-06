import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Insert project path
sys.path.insert(0, '.')

from civix_api.services.cv.biometric_engine import BiometricEngine

# Initialize engine
engine = BiometricEngine()
engine.load()

test_dir = Path("scratch/test_matrix_images")
test_dir.mkdir(parents=True, exist_ok=True)

# 1. Generate Case F: Building / No person image (solid texture / architecture)
building_img = np.zeros((400, 400, 3), dtype=np.uint8)
cv2.rectangle(building_img, (50, 100), (350, 380), (100, 100, 100), -1)
cv2.rectangle(building_img, (80, 140), (140, 200), (200, 200, 250), -1)
cv2.rectangle(building_img, (260, 140), (320, 200), (200, 200, 250), -1)
cv2.imwrite(str(test_dir / "building_no_person.jpg"), building_img)

# 2. Generate Case E: Synthetic Group Photo (combining two reference faces)
ref1_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-001.webp"
ref2_path = r"C:\data\civix_demo\biometric_demo\refs\263f32c4-30fd-40a8-b01b-6def1b47e90c\ref-001.webp"

img1 = cv2.imread(ref1_path)
img2 = cv2.imread(ref2_path)

if img1 is not None and img2 is not None:
    img1_res = cv2.resize(img1, (200, 200))
    img2_res = cv2.resize(img2, (200, 200))
    group_img = np.zeros((300, 500, 3), dtype=np.uint8)
    group_img[50:250, 30:230] = img1_res
    group_img[50:250, 270:470] = img2_res
    cv2.imwrite(str(test_dir / "group_photo.jpg"), group_img)

print("Test matrix images prepared in scratch/test_matrix_images.")

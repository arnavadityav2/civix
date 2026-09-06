import os
import sys
import hashlib
import cv2
import numpy as np
from pathlib import Path

sys.path.insert(0, '.')

from civix_api.services.cv.biometric_engine import BiometricEngine

def run_test_suite():
    engine = BiometricEngine()
    engine.load()
    
    test_dir = Path("scratch/test_matrix_images")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print("===============================================================")
    print("CIVIX 2.0 BIOMETRIC DETECTION REMEDIATION — TEST MATRIX SUITE")
    print("===============================================================")

    # Test A: Clear single-person portrait (ref-001)
    ref_a = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-001.webp"
    with open(ref_a, "rb") as f:
        res_a = engine.search(f.read())
    print(f"\n[TEST A] Clear Single-Person Portrait:")
    print(f"  Status        : {res_a.get('status')}")
    print(f"  Detected Faces: {res_a.get('detected_faces')}")
    print(f"  Person Matched: {res_a.get('person_id')}")
    print(f"  Match Score   : {res_a.get('match_score')}")

    # Test B: Existing CIVIX avatar
    ref_b = r"C:\data\civix_demo\biometric_demo\refs\263f32c4-30fd-40a8-b01b-6def1b47e90c\ref-001.webp"
    with open(ref_b, "rb") as f:
        res_b = engine.search(f.read())
    print(f"\n[TEST B] Existing CIVIX Avatar:")
    print(f"  Status        : {res_b.get('status')}")
    print(f"  Detected Faces: {res_b.get('detected_faces')}")
    print(f"  Person Matched: {res_b.get('person_id')}")

    # Test C: Derived blurred CCTV-style face (ref-012)
    ref_c = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-012.webp"
    with open(ref_c, "rb") as f:
        res_c = engine.search(f.read())
    print(f"\n[TEST C] Derived Blurred CCTV-style Face:")
    print(f"  Status        : {res_c.get('status')}")
    print(f"  Detected Faces: {res_c.get('detected_faces')}")
    print(f"  Confidence Band: {res_c.get('confidence_band')}")

    # Test D: Head tilt / side variation (ref-011)
    ref_d = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-011.webp"
    with open(ref_d, "rb") as f:
        res_d = engine.search(f.read())
    print(f"\n[TEST D] Side Profile / Head Tilt Variation:")
    print(f"  Status        : {res_d.get('status')}")
    print(f"  Detected Faces: {res_d.get('detected_faces')}")

    # Test E: Group photo (2 faces)
    group_p = test_dir / "group_photo.jpg"
    with open(group_p, "rb") as f:
        res_e = engine.search(f.read())
    print(f"\n[TEST E] Group Photo (2 distinct faces):")
    print(f"  Status        : {res_e.get('status')}")
    print(f"  Detected Faces: {res_e.get('detected_faces')}")

    # Test F: Building / No person
    bld_p = test_dir / "building_no_person.jpg"
    with open(bld_p, "rb") as f:
        res_f = engine.search(f.read())
    print(f"\n[TEST F] Building / No Person:")
    print(f"  Status        : {res_f.get('status')}")
    print(f"  Detected Faces: {res_f.get('detected_faces')}")

    # Test H: Repeated upload stability
    with open(ref_a, "rb") as f:
        bytes_a = f.read()
    res_h1 = engine.search(bytes_a)
    res_h2 = engine.search(bytes_a)
    print(f"\n[TEST H] Repeated Upload Stability:")
    print(f"  Run 1 Detected Faces: {res_h1.get('detected_faces')} Score: {res_h1.get('match_score')}")
    print(f"  Run 2 Detected Faces: {res_h2.get('detected_faces')} Score: {res_h2.get('match_score')}")
    print(f"  Stable        : {res_h1 == res_h2}")

if __name__ == "__main__":
    run_test_suite()

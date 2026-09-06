import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path

models_dir = Path(r"C:\data\civix_demo\biometric_demo\models")
yunet_path = models_dir / "face_detection_yunet_2023mar.onnx"
sface_path = models_dir / "face_recognition_sface_2021dec.onnx"

print("==========================================================================")
print("CIVIX 2.0 BIOMETRIC MODEL PROVENANCE & TECHNICAL AUDIT")
print("==========================================================================")

print(f"\n1. FACE DETECTOR MODEL: {yunet_path.name}")
print(f"   Path                : {yunet_path}")
print(f"   Size                : {yunet_path.stat().st_size if yunet_path.exists() else 0} bytes")
print(f"   Source / Origin     : OpenCV Zoo (official OpenCV model repository)")
print(f"   Repository URL      : https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet")
print(f"   Model Architecture  : YuNet (CNN face detector by Shiqi Yu)")
print(f"   Model Version       : 2023mar (face_detection_yunet_2023mar.onnx)")
print(f"   License             : Apache 2.0 License (OpenCV Zoo official license)")
print(f"   Redistribution Terms: Permissive commercial and non-commercial redistribution permitted")
print(f"   Input Tensor Shape  : Dynamic [1, 3, H, W] (Set via detector.setInputSize((W, H)))")
print(f"   Output Tensor Shape : [N, 15] (where N is face proposals, [x,y,w,h, 5 landmarks(10), score])")
print(f"   Preprocessing Req   : BGR image, resized to input size, normalized internally by YuNet")

print(f"\n2. FACE RECOGNITION MODEL: {sface_path.name}")
print(f"   Path                : {sface_path}")
print(f"   Size                : {sface_path.stat().st_size if sface_path.exists() else 0} bytes")
print(f"   Source / Origin     : OpenCV Zoo (official OpenCV model repository)")
print(f"   Repository URL      : https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface")
print(f"   Model Architecture  : SFace (SphereFace / CosFace based deep feature extractor)")
print(f"   Model Version       : 2021dec (face_recognition_sface_2021dec.onnx)")
print(f"   License             : Apache 2.0 License (OpenCV Zoo official license)")
print(f"   Redistribution Terms: Permissive commercial and non-commercial redistribution permitted")
print(f"   Input Tensor Shape  : [1, 3, 112, 112] (aligned and cropped face image)")
print(f"   Output Tensor Shape : [1, 128] (128-dimensional dense floating point embedding vector)")
print(f"   Embedding Dimension : 128")
print(f"   Preprocessing Req   : Face alignment and 112x112 crop via cv2.FaceRecognizerSF.alignCrop()")
print(f"   Normalization Req   : L2 normalization on output feature vector (np.linalg.norm(feat) == 1.0)")

# Check if MobileFaceNet exists anywhere in the repository or models dir
mobilefacenet_paths = list(Path(".").glob("**/MobileFaceNet*.onnx")) + list(models_dir.glob("*Mobile*.onnx"))
print(f"\n3. MOBILEFACENET AVAILABILITY CHECK:")
print(f"   Found MobileFaceNet Files: {mobilefacenet_paths}")

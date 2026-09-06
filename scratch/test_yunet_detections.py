import cv2
import numpy as np

yunet_path = r"C:\data\civix_demo\biometric_demo\models\face_detection_yunet_2023mar.onnx"
detector = cv2.FaceDetectorYN.create(
    model=yunet_path,
    config="",
    input_size=(320, 320),
    score_threshold=0.5,
    nms_threshold=0.3,
    top_k=5000,
)

# Test with a photo if available in refs
test_img_path = r"C:\data\civix_demo\biometric_demo\refs\09d7a50a-82dd-4acf-1c8c-ed1d70f5b332\ref-001.webp"
img = cv2.imread(test_img_path)
h, w = img.shape[:2]
detector.setInputSize((w, h))
_, faces = detector.detect(img)

print("Faces detected:", len(faces) if faces is not None else 0)
if faces is not None:
    for i, face in enumerate(faces):
        print(f"Face {i+1}: bbox={face[:4]}, score={face[-1]:.4f}")

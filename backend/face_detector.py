"""
Face Detection module using SCRFD (insightface)
Detects faces and returns bounding boxes + 5-point keypoints
"""
import numpy as np
import cv2
from typing import List, Dict, Any


class FaceDetector:
    """
    SCRFD-based face detector via insightface.
    Outputs bounding boxes and 5-point facial landmarks.
    """

    def __init__(self, model_pack: str = "buffalo_sc", det_size: tuple = (640, 640)):
        from insightface.app import FaceAnalysis

        self.app = FaceAnalysis(
            name=model_pack,
            allowed_modules=["detection"],
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=0, det_size=det_size)
        self.det_size = det_size

    def detect(self, img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect faces in an image.

        Args:
            img: BGR image as numpy array

        Returns:
            List of dicts with keys:
              - bbox: [x1, y1, x2, y2] (int)
              - kps:  [[x,y], ...] 5 keypoints or None
              - score: detection confidence (float)
        """
        faces = self.app.get(img)
        results = []
        for face in faces:
            kps = face.kps.tolist() if face.kps is not None else None
            results.append(
                {
                    "bbox": face.bbox.astype(int).tolist(),
                    "kps": kps,
                    "score": float(face.det_score),
                }
            )
        # Sort by detection score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def draw(self, img: np.ndarray, results: List[Dict]) -> np.ndarray:
        """Draw bounding boxes and keypoints on image for debugging."""
        out = img.copy()
        for face in results:
            x1, y1, x2, y2 = face["bbox"]
            cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
            if face["kps"]:
                for kp in face["kps"]:
                    cv2.circle(out, (int(kp[0]), int(kp[1])), 3, (0, 0, 255), -1)
        return out

"""
Feature Extraction module using ArcFace (insightface).
Performs face alignment then extracts a normalized embedding vector.
"""
import numpy as np
from typing import Optional


class FaceRecognizer:
    """
    ArcFace-based face recognizer via insightface.
    Internally performs Similarity Transform alignment before embedding.

    Pipeline:
        raw image + 5-pt keypoints
            -> Face Alignment (warpAffine to 112×112)
            -> ArcFace backbone
            -> L2-normalized embedding (R^512)
    """

    def __init__(self, model_pack: str = "buffalo_sc"):
        from insightface.app import FaceAnalysis

        # Load the full pack so the recognition model is available
        self.app = FaceAnalysis(
            name=model_pack,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        self.app.prepare(ctx_id=0, det_size=(320, 320))

        # Grab the recognition model directly
        if "recognition" not in self.app.models:
            raise RuntimeError(
                f"No recognition model found in pack '{model_pack}'. "
                "Try 'buffalo_l' or 'buffalo_sc'."
            )
        self._rec = self.app.models["recognition"]

    def get_embedding(self, img: np.ndarray, kps) -> np.ndarray:
        """
        Align face and extract embedding.

        Args:
            img: Full BGR frame
            kps: 5-point facial keypoints [[x,y], ...] (list or ndarray)

        Returns:
            L2-normalized embedding vector of shape (d,)
        """
        from insightface.utils import face_align

        kps_arr = np.array(kps, dtype=np.float32)
        aligned = face_align.norm_crop(img, landmark=kps_arr, image_size=112)
        feat = self._rec.get_feat(aligned).flatten()
        norm = np.linalg.norm(feat)
        return feat / norm if norm > 0 else feat

    @property
    def embedding_dim(self) -> int:
        """Dimensionality of the embedding vector."""
        return self._rec.output_shape[-1] if hasattr(self._rec, "output_shape") else 512

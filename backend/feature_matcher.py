"""
Feature Matching module using FAISS.
Stores face embeddings and performs cosine similarity search.
"""
import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np

logger = logging.getLogger(__name__)


class FeatureMatcher:
    """
    FAISS-based vector store for face embeddings.

    Uses IndexFlatIP (inner product) with L2-normalized vectors,
    which is equivalent to cosine similarity.

    Similarity threshold τ: faces above threshold are identified,
    below → "unknown".
    """

    def __init__(self, embedding_dim: int = 512, threshold: float = 0.4):
        self.embedding_dim = embedding_dim
        self.threshold = threshold

        # IndexFlatIP: exact nearest-neighbour search via inner product
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.id_map: List[str] = []          # position i → identity name
        self.metadata: Dict[str, List[int]] = {}  # name → list of vector positions

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def add(self, name: str, embedding: np.ndarray) -> int:
        """
        Add one embedding to the database.

        Returns the internal index position assigned.
        """
        vec = self._normalize(embedding)
        idx = self.index.ntotal
        self.index.add(vec)
        self.id_map.append(name)
        self.metadata.setdefault(name, []).append(idx)
        return idx

    def search(self, embedding: np.ndarray, k: int = 1) -> Tuple[Optional[str], float]:
        """
        Find the best matching identity.

        Returns:
            (name, similarity) where name is None when db is empty,
            or "unknown" when similarity < threshold.
        """
        if self.index.ntotal == 0:
            return None, 0.0

        vec = self._normalize(embedding)
        sims, idxs = self.index.search(vec, min(k, self.index.ntotal))

        best_sim = float(sims[0][0])
        best_idx = int(idxs[0][0])

        if best_sim >= self.threshold and best_idx >= 0:
            return self.id_map[best_idx], best_sim
        return "unknown", best_sim

    def remove(self, name: str) -> bool:
        """
        Remove all embeddings for an identity.
        Requires a full index rebuild — O(N).
        """
        if name not in self.metadata:
            return False

        positions_to_remove = set(self.metadata[name])
        new_id_map = []
        vectors = []

        for i, iname in enumerate(self.id_map):
            if i not in positions_to_remove:
                vec = np.zeros(self.embedding_dim, dtype=np.float32)
                self.index.reconstruct(i, vec)
                vectors.append(vec)
                new_id_map.append(iname)

        # Rebuild
        self.index = faiss.IndexFlatIP(self.embedding_dim)
        if vectors:
            self.index.add(np.stack(vectors).astype(np.float32))

        self.id_map = new_id_map
        del self.metadata[name]

        # Re-index metadata positions
        self.metadata = {}
        for i, iname in enumerate(self.id_map):
            self.metadata.setdefault(iname, []).append(i)

        return True

    def list_identities(self) -> List[str]:
        return list(self.metadata.keys())

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, directory: str):
        """Save FAISS index + id_map to disk."""
        os.makedirs(directory, exist_ok=True)
        faiss.write_index(self.index, os.path.join(directory, "face.index"))
        with open(os.path.join(directory, "meta.json"), "w") as f:
            json.dump(
                {
                    "id_map": self.id_map,
                    "metadata": self.metadata,
                    "embedding_dim": self.embedding_dim,
                    "threshold": self.threshold,
                },
                f,
                indent=2,
            )
        logger.info("Saved %d vectors to %s", self.index.ntotal, directory)

    def load(self, directory: str):
        """Load FAISS index + id_map from disk."""
        index_path = os.path.join(directory, "face.index")
        meta_path = os.path.join(directory, "meta.json")
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            logger.info("No existing database found at %s — starting fresh.", directory)
            return
        self.index = faiss.read_index(index_path)
        with open(meta_path) as f:
            data = json.load(f)
        self.id_map = data["id_map"]
        self.metadata = data["metadata"]
        self.embedding_dim = data.get("embedding_dim", self.embedding_dim)
        self.threshold = data.get("threshold", self.threshold)
        logger.info("Loaded %d vectors from %s", self.index.ntotal, directory)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        vec = embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(vec)
        return vec

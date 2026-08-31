"""Exact dense text retrieval in RAM over the immutable catalog."""
from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path

from solution.retrieval.onnx_models import LocalModel, MODELS, sha256


class DenseIndex:
    def __init__(self, directory: Path, catalog_path: Path) -> None:
        import numpy as np

        self.np = np
        manifest = json.loads((directory / "index-manifest.json").read_text(encoding="utf-8"))
        if manifest.get("catalog_sha256") != sha256(catalog_path):
            raise ValueError("dense catalog checksum mismatch")
        if manifest.get("model_revision") != MODELS["embedding"][1] or manifest.get("dimensions") != 384:
            raise ValueError("unsupported dense artifact")
        for name in ("vectors.npy", "ids.json"):
            if manifest.get("sha256", {}).get(name) != sha256(directory / name):
                raise ValueError("dense artifact checksum mismatch")
        if manifest.get("model_manifest_sha256") != sha256(directory / "embedding/manifest.json"):
            raise ValueError("dense embedding model changed")
        self.ids = json.loads((directory / "ids.json").read_text(encoding="utf-8"))
        if not all(isinstance(value, str) for value in self.ids) or len(set(self.ids)) != len(self.ids):
            raise ValueError("invalid dense IDs")
        self.vectors = np.load(directory / "vectors.npy", allow_pickle=False)  # no mmap: all in memory
        if self.vectors.dtype != np.float32 or self.vectors.shape != (len(self.ids), 384) or not np.isfinite(self.vectors).all():
            raise ValueError("invalid dense matrix")
        if len(self.ids) != manifest.get("products") or not np.allclose(np.linalg.norm(self.vectors, axis=1), 1, atol=1e-4):
            raise ValueError("dense matrix not normalized")
        self.encoder = LocalModel(directory / "embedding", "embedding")
        self.positions = {identifier: index for index, identifier in enumerate(self.ids)}
        self.cache = OrderedDict()

    def search(self, query: str, limit: int) -> list[tuple[str, float]]:
        if not query.strip() or limit <= 0:
            return []
        query = query[:8000]
        key = query, min(limit, len(self.ids))
        if key in self.cache:
            self.cache.move_to_end(key)
            return list(self.cache[key])
        vector = self.encoder.predict([query])[0]
        # einsum avoids uncontrolled BLAS thread pools on a small laptop matrix.
        scores = self.np.einsum("ij,j->i", self.vectors, vector, optimize=False)
        # Stable complete sort makes equal-score selection deterministic too.
        order = self.np.argsort(-scores, kind="stable")[:key[1]]
        rows = [(self.ids[int(index)], float(scores[index])) for index in order]
        self.cache[key] = tuple(rows)
        if len(self.cache) > 128:
            self.cache.popitem(last=False)
        return rows

    def similarity(self, left: str, right: str) -> float:
        """Catalog-vector similarity for bounded browsing diversification."""
        return float(self.vectors[self.positions[left]] @ self.vectors[self.positions[right]])

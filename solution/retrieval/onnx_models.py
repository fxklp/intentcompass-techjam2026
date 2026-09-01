"""Local-only pretrained inference. No downloads, training, or remote code."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


MODELS = {
    "embedding": ("sentence-transformers/all-MiniLM-L6-v2", "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"),
    "reranker": ("cross-encoder/ms-marco-MiniLM-L6-v2", "233902d25c440f23af6f7d6e94d2946bac0bee0a"),
}
MODEL_FILES = ("onnx/model_quint8_avx2.onnx", "tokenizer.json", "README.md")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1048576), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_model(directory: Path, kind: str) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    repository, revision = MODELS[kind]
    if manifest.get("repository") != repository or manifest.get("revision") != revision:
        raise ValueError("unexpected model provenance")
    if set(manifest.get("sha256", {})) != set(MODEL_FILES):
        raise ValueError("incomplete model manifest")
    for name in MODEL_FILES:
        if sha256(directory / name) != manifest["sha256"][name]:
            raise ValueError("model file checksum mismatch")
    return manifest


class LocalModel:
    def __init__(self, directory: Path, kind: str, *, threads: int = 2) -> None:
        import numpy as np
        import onnxruntime as ort
        from tokenizers import Tokenizer

        self.manifest = verify_model(directory, kind)
        self.kind = kind
        self.np = np
        self.tokenizer = Tokenizer.from_file(str(directory / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=256)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")
        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, min(4, threads))
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self.session = ort.InferenceSession(str(directory / MODEL_FILES[0]), sess_options=options, providers=["CPUExecutionProvider"])
        self.inputs = {value.name for value in self.session.get_inputs()}

    def predict(self, texts: list) -> object:
        np = self.np
        if not texts:
            return np.empty((0, 384), dtype=np.float32) if self.kind == "embedding" else np.empty(0, dtype=np.float32)
        encoded = self.tokenizer.encode_batch(texts)
        inputs = {
            "input_ids": np.asarray([row.ids for row in encoded], dtype=np.int64),
            "attention_mask": np.asarray([row.attention_mask for row in encoded], dtype=np.int64),
            "token_type_ids": np.asarray([row.type_ids for row in encoded], dtype=np.int64),
        }
        output = self.session.run(None, {key: value for key, value in inputs.items() if key in self.inputs})[0]
        if self.kind == "reranker":
            scores = np.asarray(output, dtype=np.float32).reshape(-1)
            if scores.shape != (len(texts),) or not np.isfinite(scores).all():
                raise ValueError("invalid cross-encoder scores")
            return scores
        mask = inputs["attention_mask"][..., None]
        vectors = (output * mask).sum(axis=1) / np.maximum(mask.sum(axis=1), 1)
        vectors = np.asarray(vectors, dtype=np.float32)
        if vectors.shape != (len(texts), 384) or not np.isfinite(vectors).all():
            raise ValueError("invalid embedding output")
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        if (norms < 1e-8).any():
            raise ValueError("zero embedding")
        return vectors / norms

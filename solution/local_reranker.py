"""Optional pretrained cross-encoder, not an LLM and not automatically enabled."""
from pathlib import Path

from solution.retrieval.onnx_models import LocalModel
from solution.semantic import SemanticResult, safe_context


class LocalReranker:
    def __init__(self, assets: Path) -> None:
        self.enabled = True
        self.model = None
        try:
            self.model = LocalModel(assets / "reranker", "reranker")
        except Exception:
            pass

    def rerank(self, candidates: list, context: dict) -> SemanticResult:
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if self.model is None or len(candidates) < 2:
            return SemanticResult(candidates, "local_model_unavailable", usage)
        clean = safe_context(context)
        query = " ".join([clean["category"], *(value for values in clean["explicit"].values() for value in values)])[:4000]
        window = candidates[:20]
        try:
            scores = self.model.predict([(query, item.searchable_text[:4000]) for item in window])
            order = sorted(range(len(window)), key=lambda index: (-float(scores[index]), index))
        except Exception:
            self.model = None
            return SemanticResult(candidates, "local_model_failed_fallback", usage)
        return SemanticResult([*(window[index] for index in order), *candidates[20:]], "cross_encoder_ranked", usage)

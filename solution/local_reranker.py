"""Bounded pretrained cross-encoder; semantic, but explicitly not an LLM."""
import os
from pathlib import Path

from solution.retrieval.onnx_models import LocalModel
from solution.semantic import SemanticResult, safe_context


class LocalReranker:
    def __init__(self, assets: Path) -> None:
        self.enabled = True
        self.model = None
        self.calls = 0
        self.max_calls = max(0, min(64, int(os.environ.get("INTENTCOMPASS_LOCAL_RERANK_MAX_CALLS", "8"))))
        try:
            self.model = LocalModel(assets / "reranker", "reranker")
        except Exception:
            pass

    def rerank(self, candidates: list, context: dict) -> SemanticResult:
        usage = {"prompt_tokens": 0, "completion_tokens": 0}
        if self.model is None or len(candidates) < 2:
            return SemanticResult(candidates, "local_model_unavailable", usage)
        clean = safe_context(context)
        if sum(len(values) for values in clean["explicit"].values()) < 2:
            return SemanticResult(candidates, "local_model_insufficient_intent", usage)
        if self.calls >= self.max_calls:
            return SemanticResult(candidates, "local_model_call_budget_exhausted", usage)
        query = " ".join([clean["category"], *(value for values in clean["explicit"].values() for value in values)])[:4000]
        window = candidates[:20]
        self.calls += 1
        try:
            scores = self.model.predict([(query, item.searchable_text[:4000]) for item in window])
            order = sorted(range(len(window)), key=lambda index: (-float(scores[index]), index))
        except Exception:
            self.model = None
            return SemanticResult(candidates, "local_model_failed_fallback", usage, True)
        return SemanticResult([*(window[index] for index in order), *candidates[20:]], "cross_encoder_ranked", usage, True)

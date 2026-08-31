"""Construction-time feature selection; default stays the reviewed baseline."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CoreConfig:
    mode: str = "baseline"
    retrieval: str = "baseline"

    @classmethod
    def from_environment(cls) -> "CoreConfig":
        mode = os.environ.get("INTENTCOMPASS_AGENT_MODE", "baseline").strip().lower()
        retrieval = os.environ.get("INTENTCOMPASS_RETRIEVAL", "baseline").strip().lower()
        if mode not in {"baseline", "adaptive", "integrated"}:
            raise ValueError("INTENTCOMPASS_AGENT_MODE must be baseline, adaptive or integrated")
        if retrieval not in {"baseline", "dual_route", "hybrid"}:
            raise ValueError("INTENTCOMPASS_RETRIEVAL must be baseline, dual_route or hybrid")
        if mode == "baseline" and retrieval != "baseline":
            raise ValueError("dual_route requires explicit adaptive mode")
        return cls(mode, retrieval)

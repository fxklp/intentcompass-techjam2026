"""Construction-time selection; conservative offline integration by default."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CoreConfig:
    mode: str = "integrated"
    retrieval: str = "baseline"

    @classmethod
    def from_environment(cls) -> "CoreConfig":
        mode = os.environ.get("INTENTCOMPASS_AGENT_MODE", "integrated").strip().lower()
        retrieval = os.environ.get("INTENTCOMPASS_RETRIEVAL", "capability").strip().lower()
        if mode not in {"baseline", "adaptive", "integrated"}:
            raise ValueError("INTENTCOMPASS_AGENT_MODE must be baseline, adaptive or integrated")
        if retrieval not in {"baseline", "dual_route", "hybrid", "capability"}:
            raise ValueError("INTENTCOMPASS_RETRIEVAL must be baseline, dual_route, hybrid or capability")
        if mode == "baseline" and retrieval != "baseline":
            raise ValueError("dual_route requires explicit adaptive mode")
        return cls(mode, retrieval)

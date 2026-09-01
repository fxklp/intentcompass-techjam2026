"""Run the unchanged official evaluator with the frozen offline environment.

All CLI arguments are forwarded without rewriting data, scores or outputs.
Unlike release_check, this does not assert Public-set reference metrics.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.release_check import activate_preset


if __name__ == "__main__":
    activate_preset()
    runpy.run_module("evaluator.local_evaluator", run_name="__main__")

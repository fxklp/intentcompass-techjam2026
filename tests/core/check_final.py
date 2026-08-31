"""Isolated final-integration proof: immutable inputs, aggregate-only Shadow."""
from __future__ import annotations

import argparse
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path

from tests.core.check_adaptive import ROOT, sha256, worker, write_json


def pin_first_cpu() -> int:
    """Pin only this benchmark child to its first allowed CPU, not the host."""
    import ctypes
    from ctypes import wintypes
    import os
    if os.name == "nt":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.GetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(ctypes.c_size_t)]
        kernel.GetProcessAffinityMask.restype = wintypes.BOOL
        kernel.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
        kernel.SetProcessAffinityMask.restype = wintypes.BOOL
        handle = kernel.GetCurrentProcess()
        allowed, system = ctypes.c_size_t(), ctypes.c_size_t()
        if not kernel.GetProcessAffinityMask(handle, ctypes.byref(allowed), ctypes.byref(system)):
            raise ctypes.WinError(ctypes.get_last_error())
        mask = allowed.value & -allowed.value
        if not mask or not kernel.SetProcessAffinityMask(handle, mask):
            raise ctypes.WinError(ctypes.get_last_error())
        return mask
    if hasattr(os, "sched_getaffinity"):
        cpu = min(os.sched_getaffinity(0))
        os.sched_setaffinity(0, {cpu})
        return 1 << cpu
    raise RuntimeError("controlled CPU affinity is unsupported on this platform")


def inventory(root: Path = ROOT) -> dict:
    paths = [root / "data/catalog.jsonl", root / "data/public_set.jsonl"]
    for directory in ("solution", "starter", "evaluator", "tests/core"):
        paths.extend(sorted((root / directory).rglob("*.py")))
    paths.extend(sorted((root / "scripts").glob("*.py")))
    return {path.relative_to(root).as_posix(): sha256(path) for path in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("baseline", "adaptive", "integrated"), default="integrated")
    parser.add_argument("--retrieval", choices=("baseline", "dual_route", "hybrid"), default="baseline")
    parser.add_argument("--semantic", choices=("off", "local"), default="off")
    parser.add_argument("--split", choices=("public", "shadow"), default="public")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--reference-root", type=Path)
    parser.add_argument("--pin-first-cpu", action="store_true")
    args = parser.parse_args()
    if args.worker:
        affinity = pin_first_cpu() if args.pin_first_cpu else None
        from experiments.retrieval.evaluate import peak_rss_bytes
        from unittest.mock import patch
        from starter.agent import Agent
        constructed = []
        def observed_agent(*items, **keywords):
            agent = Agent(*items, **keywords)
            constructed.append(agent)
            return agent
        target = "scripts.benchmark_runtime.Agent" if args.split == "public" else "scripts.shadow_evaluator.Agent"
        with patch(target, side_effect=observed_agent):
            result = worker(args.split)
        adaptive = constructed[0]._core._adaptive if constructed else None
        result["effective_backend"] = {
            "core": adaptive.mode if adaptive else "baseline",
            "dense_status": getattr(adaptive.retriever, "dense_status", "not_requested") if adaptive else "not_requested",
            "semantic_component": type(adaptive.semantic).__name__ if adaptive else "disabled",
            "local_model_failed": (adaptive.semantic.model is None) if adaptive and type(adaptive.semantic).__name__ == "LocalReranker" else False,
        }
        result["peak_memory_bytes"] = peak_rss_bytes()
        result["pid"] = os.getpid()
        result["cpu_affinity_mask"] = affinity
        print(json.dumps(result))
        return
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports/generated").resolve()):
        parser.error("output must be under reports/generated")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        parser.error("do not overwrite experiment evidence")
    reference = args.reference_root.resolve() if args.reference_root else ROOT
    if args.reference_root and (args.mode != "baseline" or args.split != "public" or args.semantic != "off" or args.retrieval != "baseline"):
        parser.error("external reference is only the unchanged public offline baseline")
    before = inventory(reference)
    environment = dict(os.environ, INTENTCOMPASS_AGENT_MODE=args.mode, INTENTCOMPASS_RETRIEVAL=args.retrieval, INTENTCOMPASS_SEMANTIC=args.semantic, INTENTCOMPASS_LLM_ALLOW_NETWORK="0", PYTHONHASHSEED="0")
    command = [sys.executable, "-m", "tests.core.check_final", "--worker", "--split", args.split, "--output", str(output)]
    if args.reference_root:
        command = [sys.executable, "-c", "import json,os; from pathlib import Path; from scripts.benchmark_runtime import run_benchmark; from experiments.retrieval.evaluate import peak_rss_bytes; result=run_benchmark(Path('data/catalog.jsonl'),Path('data/public_set.jsonl')); result['metrics']=result.pop('official_metrics'); result['peak_memory_bytes']=peak_rss_bytes(); result['pid']=os.getpid(); print(json.dumps(result))"]
    if args.pin_first_cpu:
        if args.reference_root:
            source = command[-1].replace("print(json.dumps(result))", "result['cpu_affinity_mask']=selected_cpu; print(json.dumps(result))")
            command[-1] = inspect.getsource(pin_first_cpu) + "\nselected_cpu=pin_first_cpu()\n" + source
        else:
            command.append("--pin-first-cpu")
    completed = subprocess.run(command, cwd=reference, env=environment, capture_output=True, text=True, encoding="utf-8", check=True)
    result = json.loads(completed.stdout)
    if before != inventory(reference):
        raise RuntimeError("source or frozen data changed during experiment")
    result["configuration"] = {"mode": args.mode, "retrieval": args.retrieval, "semantic": args.semantic, "network": False, "split": args.split}
    result["configuration"]["pin_first_cpu"] = args.pin_first_cpu
    result["source_sha256"] = before
    write_json(output, result)
    print(json.dumps({"configuration": result["configuration"], "metrics": result["metrics"], "timing": result.get("timing"), "peak_memory_bytes": result["peak_memory_bytes"], "sha256": sha256(output)}, indent=2))


if __name__ == "__main__":
    main()

"""Evaluate the explicit TASK-305 candidate with the unchanged evaluator."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluator.local_evaluator import catalog_index, evaluate, load_jsonl
from scripts.shadow_evaluator import SCENARIO_COUNTS, SEED, build_samples, select_targets
from solution.retrieval.onnx_models import sha256
from starter.agent import Agent


PRESET = {
    "INTENTCOMPASS_AGENT_MODE": "integrated",
    "INTENTCOMPASS_RETRIEVAL": "hybrid",
    "INTENTCOMPASS_OFFLINE_RANKING": "constraints",
    "INTENTCOMPASS_CATEGORY_ORDER": "off",
    "INTENTCOMPASS_PRECISION_ORDER": "off",
    "INTENTCOMPASS_FINAL_POLICY": "off",
    "INTENTCOMPASS_TERMINAL_RECOVERY": "off",
    "INTENTCOMPASS_LOCAL_RERANK_MAX_CALLS": "8",
    "INTENTCOMPASS_LOCAL_LLM_MAX_CALLS": "4",
    "PYTHONHASHSEED": "0",
}


def git_state() -> tuple[str, bool]:
    safe = ROOT.as_posix()
    commit = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "rev-parse", "HEAD"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "status", "--porcelain"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.strip()
    return commit, bool(status)


def samples_for(name: str, identifiers: set[str]) -> tuple[list[dict], str]:
    public = load_jsonl(ROOT / "data/public_set.jsonl")
    if name == "public":
        samples = public
    elif name == "shadow":
        excluded = {str(item["ground_truth"]["parent_asin"]) for item in public}
        targets = select_targets(identifiers, excluded, sum(SCENARIO_COUNTS.values()), SEED)
        samples = build_samples(targets, SEED)
    else:
        # Exact historical generator; this is reproduction, not a fresh holdout.
        from tests.core.check_final_policy import reproduction_dataset
        samples, expected = reproduction_dataset(name, identifiers)
        actual = hashlib.sha256(("\n".join(str(item["ground_truth"]["parent_asin"]) for item in samples) + "\n").encode()).hexdigest()
        if actual != expected:
            raise RuntimeError("historical dataset digest changed")
    digest = hashlib.sha256(("\n".join(str(item["ground_truth"]["parent_asin"]) for item in samples) + "\n").encode()).hexdigest()
    return samples, digest


def activate(args: argparse.Namespace) -> dict[str, str]:
    os.environ.update(PRESET)
    os.environ["INTENTCOMPASS_SEMANTIC"] = args.semantic
    os.environ["INTENTCOMPASS_LLM_ALLOW_NETWORK"] = "1" if args.allow_network else "0"
    if args.model:
        os.environ["INTENTCOMPASS_LLM_MODEL"] = args.model
    if args.assets:
        os.environ["INTENTCOMPASS_SEMANTIC_ASSETS"] = str(args.assets.resolve())
    return {key: os.environ[key] for key in (*PRESET, "INTENTCOMPASS_SEMANTIC", "INTENTCOMPASS_LLM_ALLOW_NETWORK")}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("public", "shadow", "confirm_a", "confirm_b"), default="public")
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog.jsonl")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--assets", type=Path, default=ROOT / "artifacts/semantic")
    parser.add_argument("--semantic", choices=("local_llm", "local", "qwen", "deepseek", "openai"), default="local")
    parser.add_argument("--model", default="")
    parser.add_argument("--allow-network", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    generated = (ROOT / "reports/generated").resolve()
    if output.exists() or not output.is_relative_to(generated):
        parser.error("output must be a new file below reports/generated")
    effective = activate(args)

    identifiers, categories, products = catalog_index(args.catalog)
    samples, dataset_digest = samples_for(args.dataset, identifiers)
    started = time.perf_counter()
    agent = Agent(args.catalog)
    controller = agent._core._adaptive
    if controller.retriever.dense_status != "ready":
        agent.close()
        raise RuntimeError(f"TASK-305 requires real dense assets; status={controller.retriever.dense_status}")
    if args.semantic == "local" and getattr(controller.semantic, "model", None) is None:
        agent.close()
        raise RuntimeError("TASK-305 local semantic model is unavailable")
    if args.semantic == "local_llm" and not controller.semantic.enabled:
        agent.close()
        raise RuntimeError("TASK-305 local LLM runtime/model is unavailable")
    try:
        metrics = evaluate(agent, samples, identifiers, categories, products)
        evidence = dict(sorted(controller.evidence_counts.items()))
    finally:
        agent.close()
    llm = args.semantic in {"local_llm", "qwen", "deepseek", "openai"}
    if llm and evidence.get("semantic:model_ranked", 0) == 0:
        raise RuntimeError("configured LLM produced no validated ranking; capability is not complete")
    if args.semantic == "local" and evidence.get("semantic:cross_encoder_ranked", 0) == 0:
        raise RuntimeError("configured cross-encoder produced no ranking; semantic capability is not active")

    commit, dirty = git_state()
    asset_manifest = args.assets / "index-manifest.json"
    report = {
        "schema_version": 1,
        "task": "TASK-305",
        "candidate_complete_except_llm": not llm,
        "llm_semantic_validated": llm,
        "commit": commit,
        "working_tree_dirty": dirty,
        "python": platform.python_version(),
        "dataset": args.dataset,
        "dataset_target_sha256": dataset_digest,
        "catalog_sha256": sha256(args.catalog),
        "effective_configuration": effective,
        "model": ("Qwen/Qwen2.5-1.5B-Instruct-GGUF@91cad51170dc346986eccefdc2dd33a9da36ead9 via llama.cpp b10516" if args.semantic == "local_llm" else args.model) if llm else "cross-encoder/ms-marco-MiniLM-L6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a (non-LLM)",
        "semantic_index_manifest_sha256": sha256(asset_manifest),
        "capability_evidence": evidence,
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        "metrics": metrics,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({**{key: report[key] for key in report if key not in {"metrics", "capability_evidence"}}, "capability_evidence": evidence, "metrics": {key: value for key, value in metrics.items() if key != "sessions"}}, indent=2))
    print("sha256=" + sha256(output))


if __name__ == "__main__":
    main()

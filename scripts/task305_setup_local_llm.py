"""Download and verify the pinned local TASK-305 LLM runtime and model."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_URL = "https://github.com/ggml-org/llama.cpp/releases/download/b10516/llama-b10516-bin-win-cpu-x64.zip"
RUNTIME_SHA256 = "fbbbc55e0eb2e1b07f9dcb9488616c98ed47d9003b90e15e7c8c7812c4307cd3"
MODEL_REVISION = "91cad51170dc346986eccefdc2dd33a9da36ead9"
MODEL_URL = f"https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/{MODEL_REVISION}/qwen2.5-1.5b-instruct-q4_k_m.gguf"
MODEL_SHA256 = "6a1a2eb6d15622bf3c96857206351ba97e1af16c30d7a74ee38970e434e9407e"
MODEL_BYTES = 1_117_320_736


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download(url: str, destination: Path, expected: str, expected_bytes: int | None = None) -> None:
    if destination.exists():
        if sha256(destination) != expected:
            raise ValueError(f"cached hash mismatch: {destination}")
        return
    partial = destination.with_suffix(destination.suffix + ".partial")
    request = urllib.request.Request(url, headers={"User-Agent": "IntentCompass-TASK305/1"})
    with urllib.request.urlopen(request, timeout=60) as response, partial.open("wb") as output:
        shutil.copyfileobj(response, output, 1024 * 1024)
    if expected_bytes is not None and partial.stat().st_size != expected_bytes:
        partial.unlink(missing_ok=True)
        raise ValueError("downloaded size mismatch")
    if sha256(partial) != expected:
        partial.unlink(missing_ok=True)
        raise ValueError("downloaded SHA256 mismatch")
    partial.replace(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/local_llm")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("output must be under ignored artifacts/")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "llama-b10516-bin-win-cpu-x64.zip"
    model = output / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    download(RUNTIME_URL, archive, RUNTIME_SHA256)
    download(MODEL_URL, model, MODEL_SHA256, MODEL_BYTES)
    runtime = output / "runtime"
    executable = runtime / "llama-cli.exe"
    if not executable.exists():
        runtime.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as bundle:
            unsafe = [name for name in bundle.namelist() if Path(name).is_absolute() or ".." in Path(name).parts]
            if unsafe:
                raise ValueError("unsafe runtime archive")
            bundle.extractall(runtime)
    if not executable.exists():
        raise FileNotFoundError("llama-cli.exe missing from verified runtime")
    manifest = {
        "schema_version": 1,
        "runtime": {"repository": "ggml-org/llama.cpp", "tag": "b10516", "license": "MIT", "archive_sha256": RUNTIME_SHA256},
        "model": {"repository": "Qwen/Qwen2.5-1.5B-Instruct-GGUF", "revision": MODEL_REVISION, "license": "Apache-2.0", "file_sha256": MODEL_SHA256, "bytes": MODEL_BYTES},
        "paths": {"executable": "runtime/llama-cli.exe", "model": model.name},
    }
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(manifest, indent=2))
    print("manifest_sha256=" + sha256(manifest_path))


if __name__ == "__main__":
    if sys.platform != "win32":
        raise SystemExit("this pinned setup command is Windows-only; use a verified llama.cpp build for the host platform")
    main()

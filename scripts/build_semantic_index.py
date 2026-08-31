"""Explicit setup of pinned text-only CPU assets and catalog-derived vectors."""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from solution.contracts import flatten_text
from solution.retrieval.onnx_models import LocalModel, MODELS, MODEL_FILES, sha256, verify_model


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def download_model(directory: Path, kind: str) -> None:
    repository, revision = MODELS[kind]
    if (directory / "manifest.json").exists():
        verify_model(directory, kind)
        print(f"Verified cached {kind}", flush=True)
        return
    directory.mkdir(parents=True, exist_ok=True)
    for filename in MODEL_FILES:
        path = directory / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".partial")
        print(f"Downloading pinned {kind}: {filename}", flush=True)
        with urlopen(f"https://huggingface.co/{repository}/resolve/{revision}/{filename}", timeout=60) as response, temporary.open("wb") as output:
            while block := response.read(1048576):
                output.write(block)
        temporary.replace(path)
    write_json(directory / "manifest.json", {"repository": repository, "revision": revision, "license": "Apache-2.0", "sha256": {name: sha256(directory / name) for name in MODEL_FILES}})


def build(catalog: Path, output: Path, batch_size: int) -> None:
    import numpy as np

    started = time.perf_counter()
    catalog_hash = sha256(catalog)
    encoder = LocalModel(output / "embedding", "embedding")
    ids, batches, texts = [], [], []
    with catalog.open(encoding="utf-8") as handle:
        for line in handle:
            product = json.loads(line)
            ids.append(str(product["parent_asin"]))
            # Title/category first, then factual catalog attributes; never labels.
            texts.append(" ".join(flatten_text(product.get(key)) for key in ("title", "categories", "features", "details", "description"))[:8000])
            if len(texts) == batch_size:
                batches.append(encoder.predict(texts))
                texts.clear()
                if len(ids) % (batch_size * 50) == 0:
                    print(f"Encoded {len(ids)} products in {time.perf_counter()-started:.1f}s", flush=True)
    if texts:
        batches.append(encoder.predict(texts))
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("empty catalog or duplicate IDs")
    if sha256(catalog) != catalog_hash:
        raise ValueError("catalog changed during build")
    vectors = np.concatenate(batches)
    np.save(output / "vectors.npy", vectors, allow_pickle=False)
    write_json(output / "ids.json", ids)
    write_json(output / "index-manifest.json", {
        "schema_version": 1, "catalog_sha256": catalog_hash, "products": len(ids),
        "dimensions": 384, "dtype": "float32", "pooling": "attention_mask_mean_l2",
        "max_tokens": 256, "text_fields": ["title", "categories", "features", "details", "description"],
        "model_revision": MODELS["embedding"][1], "model_manifest_sha256": sha256(output / "embedding/manifest.json"),
        "sha256": {name: sha256(output / name) for name in ("vectors.npy", "ids.json")},
        "build_seconds": round(time.perf_counter()-started, 3), "python": platform.python_version(),
    })
    print(f"Index built: {len(ids)} products, {vectors.nbytes} vector bytes", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "data/catalog.jsonl")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/semantic")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--assets-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=32)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "artifacts").resolve()):
        parser.error("output must be inside ignored artifacts directory")
    if not 1 <= args.batch_size <= 64:
        parser.error("batch size must be 1..64")
    output.mkdir(parents=True, exist_ok=True)
    if args.download:
        for kind in MODELS:
            download_model(output / kind, kind)
    if not args.assets_only:
        build(args.catalog.resolve(), output, args.batch_size)


if __name__ == "__main__":
    main()

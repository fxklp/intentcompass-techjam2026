from __future__ import annotations

import argparse
import gzip
import hashlib
import shutil
import sys
import urllib.request
from pathlib import Path


CATALOG_URL = (
    "https://github.com/TechJam2026/techjam-conversational-search/"
    "releases/download/participant-kit/catalog.jsonl.gz"
)
ARCHIVE_SHA256 = "07fd142631fd6b03e2b4d09988c3eb7d53720e9d57010c79db48eeaada50a8f8"
CATALOG_SHA256 = "da979b05a68af864cb0dcf9ee6a81c010c7e66a57978ad286c7a2e005fc69a67"
CHUNK_SIZE = 1024 * 1024


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, label: str) -> None:
    actual = file_sha256(path)
    if actual != expected:
        raise RuntimeError(
            f"{label} SHA-256 mismatch: expected {expected}, got {actual}. "
            f"Remove {path} and retry."
        )


def download_catalog(destination: Path) -> Path:
    destination = destination.resolve()
    if destination.exists():
        require_hash(destination, CATALOG_SHA256, "existing catalog")
        print(f"Catalog already verified: {destination}")
        return destination

    release_dir = destination.parent / "releases"
    release_dir.mkdir(parents=True, exist_ok=True)
    archive = release_dir / "catalog.jsonl.gz"
    partial = release_dir / "catalog.jsonl.gz.part"
    extracted = destination.with_suffix(destination.suffix + ".part")

    try:
        if archive.exists():
            require_hash(archive, ARCHIVE_SHA256, "cached archive")
        else:
            print(f"Downloading official catalog from:\n{CATALOG_URL}")
            request = urllib.request.Request(
                CATALOG_URL,
                headers={"User-Agent": "IntentCompass-TechJam2026"},
            )
            with (
                urllib.request.urlopen(request, timeout=60) as response,
                partial.open("wb") as output,
            ):
                shutil.copyfileobj(response, output, CHUNK_SIZE)
            require_hash(partial, ARCHIVE_SHA256, "downloaded archive")
            partial.replace(archive)

        destination.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(archive, "rb") as source, extracted.open("wb") as output:
            shutil.copyfileobj(source, output, CHUNK_SIZE)
        require_hash(extracted, CATALOG_SHA256, "extracted catalog")
        extracted.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
        extracted.unlink(missing_ok=True)

    print(f"Catalog ready and verified: {destination}")
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download and verify the official Track 4 product catalog."
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=Path("data/catalog.jsonl"),
        help="catalog output path (default: data/catalog.jsonl)",
    )
    args = parser.parse_args()
    try:
        download_catalog(args.destination)
    except (OSError, RuntimeError) as exc:
        print(f"SETUP FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()

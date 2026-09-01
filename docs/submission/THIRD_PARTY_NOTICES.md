# Third-party data, models and libraries

IntentCompass code is original team work built on organizer-provided interfaces
and legally accessible open-source/runtime components. No third-party source
code is copied into the solution.

## Data

- Competition catalog and sessions: organizer-provided, derived from
  [Amazon Reviews 2023](https://amazon-reviews-2023.github.io/), selected
  `Clothing_Shoes_and_Jewelry` category. See `DATA_ATTRIBUTION.md`.

## Local models

- `sentence-transformers/all-MiniLM-L6-v2`, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, Apache-2.0.
- `cross-encoder/ms-marco-MiniLM-L6-v2`, revision
  `233902d25c440f23af6f7d6e94d2946bac0bee0a`, Apache-2.0.

The setup script downloads the pinned artifacts and model cards; generated
model files and the catalog-derived dense index are excluded from Git.

## Python libraries

- NumPy 2.2.6 — BSD-3-Clause
- ONNX Runtime 1.29.0 — MIT
- Hugging Face Tokenizers 0.23.1 — Apache-2.0
- Python/SQLite FTS5 — standard runtime components subject to their upstream terms

## Optional services and development tools

- Qwen/DashScope and DeepSeek compatible APIs were evaluated under their
  provider terms. They are optional and not needed for Public reproduction.
- GitHub, GitHub Actions, Codex and other AI coding assistance supported team
  development and QA. No service credential is committed.

The final YouTube video must use only team-created graphics/recordings or
properly licensed assets. No third-party music or brand logo is required.

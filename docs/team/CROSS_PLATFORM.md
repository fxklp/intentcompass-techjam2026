# Cross-Platform Collaboration Standards

To ensure a consistent developer experience across Windows, macOS, and Linux, this project enforces the following cross-platform contract:

1. **Line Ending Standard**: All text files (Python, Markdown, JSON, YAML, etc.) must use `LF (\n)` line endings. This is strictly enforced by `.editorconfig` and `.gitattributes` .
2. **Binary Safety**: Binary files such as images (PNG/JPG) and PDFs are strictly forbidden from having their line endings converted by Git.
3. **Automated Verification**: GitHub Actions will run tests and gates concurrently across a matrix of `ubuntu-latest`, `macos-latest`,and `windows-latest`.

## Reproduction Commands

To ensure the local environment is not disrupted by line ending issues, developers can run the following commands to verify:

**macOS / Linux:**
```bash
# 1. Setup Data (Network Required)
python3 scripts/setup_data.py

# 2. Evaluation and Gates (Offline)
python3 -m unittest discover -s tests -p "test_*.py"
python3 demo/run_demo.py
python3 scripts/team_gate.py --full-eval
```
**Windows (PowerShell):**
```bash
# 1. Setup Data (Network Required)
python scripts\setup_data.py

# 2. Evaluation and Gates (Offline)
python -m unittest discover -s tests -p "test_*.py"
python demo\run_demo.py
python scripts\team_gate.py --full-eval
```

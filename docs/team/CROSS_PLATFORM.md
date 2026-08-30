# Cross-Platform Collaboration Standards

To ensure a consistent developer experience across Windows, macOS, and Linux, this project enforces the following cross-platform contract:

1. **Line Ending Standard**: All text files (Python, Markdown, JSON, YAML, etc.) must use `LF (\n)` line endings. This is strictly enforced by `.editorconfig` and `.gitattributes` .
2. **Binary Safety**: Binary files such as images (PNG/JPG) and PDFs are strictly forbidden from having their line endings converted by Git.
3. **Automated Verification**: GitHub Actions will run tests and gates concurrently across a matrix of `ubuntu-latest`, `macos-latest`,and `windows-latest`.

## Reproduction Commands

To ensure the local environment is not disrupted by line ending issues, developers can run the following commands to verify:

**macOS / Linux:**
```bash
python3 scripts/setup_data.py
python3 -m unittest discover -s tests -p "test_*.py"
```
**Windows (PowerShell):**
```bash
python scripts\setup_data.py
python -m unittest discover -s tests -p "test_*.py"
```
### Step 3: Local Verification and Push to Cloud
Run the following commands in the terminal sequentially for final complete verification and push (since the temporary repository test was added, 32 or 33 tests should pass successfully):

```bash
python3 -m unittest discover -s tests -p "test_*.py"
python3 demo/run_demo.py
python3 scripts/team_gate.py --full-eval
git add tests/test_cross_platform_contract.py docs/team/CROSS_PLATFORM.md
git commit -m "test: strengthen cross-platform contract with temp repo & repro docs"
git push
git rev-parse HEAD
```

# TASK-102: whitespace gate file-level coverage

Owner: Liu Chunyi (L223233)

Reviewer: Cheng Xianyun (shinecloud9)

## Allowed paths
- `tests/test_team_gate.py`
- `docs/team/tasks/TASK-102-whitespace-gate-coverage.md`

## Outcome
Add comprehensive unit tests for the `check_text_whitespace` function to ensure:
1. Actual reading of UTF-8 files detects trailing whitespaces/tabs.
2. Clean files return no violations.
3. Invalid UTF-8 encoded files are safely ignored without crashing the gate.
4. Non-existent files and non-text files are safely ignored.
# TASK-103: Cross-platform release gate

Owner: Liu Chunyi (L223233)

## Allowed paths
- `.gitattributes`
- `.editorconfig`
- `.github/workflows/**`
- `tests/test_cross_platform_contract.py`
- `docs/team/CROSS_PLATFORM.md`
- `docs/team/tasks/TASK-103-cross-platform-release.md`

## Outcome
- **Objective**: Establish consistent cross-platform repo standards.
- **Rules applied**: `.gitattributes` (LF and binary declarations), `.editorconfig`.
- **CI**: Added GitHub Actions matrix for Windows, macOS, and Linux.
- **Verification**: Ensure 29 tests, Demo, and Team Gate pass on all systems without touching algorithms or data.
